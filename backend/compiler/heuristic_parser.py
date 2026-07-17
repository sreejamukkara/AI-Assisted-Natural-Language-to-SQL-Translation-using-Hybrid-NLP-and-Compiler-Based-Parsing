# REQUIRES: pip install spacy && python -m spacy download en_core_web_sm
import re
from typing import Optional
from .ast_nodes import SQLQuery, ConditionNode, JoinNode, OrderNode

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except ImportError:
    nlp = None
except Exception:
    nlp = None

def heuristic_nl_to_ast(query: str, schema: dict) -> Optional[SQLQuery]:
    """
    A heuristic, keyword-based parser that acts as a pure offline fallback.
    It pattern-matches words against the DB schema to stitch together an AST.
    """
    raw_query = query
    query = query.lower()
    
    q = SQLQuery(operation="SELECT", columns=["*"], table="")
    
    # 1. Detect Tables with basic synonyms
    tables_found = []
    synonyms = {
        "worker": "employees", "staff": "employees", "employee": "employees",
        "team": "employees", "department": "departments", "dept": "departments"
    }
    
    # Check synonyms
    for word in query.split():
        for syn, real_tbl in synonyms.items():
            if syn in word and real_tbl not in tables_found:
                tables_found.append(real_tbl)
                
    # Check exact schema names
    for table_name in schema.keys():
        if table_name in query or table_name.rstrip('s') in query:
            if table_name not in tables_found:
                tables_found.append(table_name)
                
    # Infer tables from uniquely stated columns (e.g., 'salary' => 'employees')
    for table_name, cols in schema.items():
        for col in cols:
            if col in query and len(col) > 2: # Ignore generic short matches
                if table_name not in tables_found:
                    tables_found.append(table_name)
            
    if not tables_found:
        q.table = ""
    else:
        # Prefer the base data table ('employees') over metadata ('departments') as the primary SELECT body if both discovered
        q.table = "employees" if "employees" in tables_found else tables_found[0]
    
    # 2. Detect Columns (Schema values are now lists of strings)
    cols_found = []
    for col_name in schema.get(q.table, []):
        if re.search(rf'\b{col_name}\b', query):
            cols_found.append(col_name)
            
    if "names" in query and "name" not in cols_found: cols_found.append("name")
    if cols_found:
        q.columns = cols_found

    # 3. Aggregations
    if any(w in query for w in ["how many", "count"]):
        if q.columns == ["*"] or not cols_found:
            q.columns = ["COUNT(*)"]
        else:
            q.columns = cols_found + ["COUNT(*)"]
            if not q.group_by: q.group_by = cols_found.copy()
    elif any(w in query for w in ["average", "avg"]):
        # Identify the primary column to average
        avg_col = None
        for col in sorted(cols_found, reverse=True):
            if col in ["salary", "budget", "id", "age"]:
                avg_col = col
                break
        if avg_col:
            new_cols = [c for c in cols_found if c != avg_col]
            new_cols.append(f"AVG({avg_col})")
            q.columns = new_cols
            # Auto-group by the other columns to make it valid SQL
            if len(new_cols) > 1 and not q.group_by:
                q.group_by = [c for c in cols_found if c != avg_col]
                
    # 4. Grouping
    if any(w in query for w in ["each", "per"]):
        if "department" in query:
            q.group_by = ["department_id" if "department_id" in schema.get(q.table, []) else "department"]
            if q.columns == ["*"]: q.columns = ["department_id", "COUNT(*)"]
            
    if "group by" in query:
        match = re.search(r'group by ([a-zA-Z_]+)', query)
        if match:
            col = match.group(1)
            q.group_by = [col]
            if q.columns == ["*"]: q.columns = [col, "COUNT(*)"]
            
    # 5. Top-N Filters
    if any(w in query for w in ["highest", "biggest", "most", "maximum", "top"]):
        ob_col = "salary" if "paid" in query or "salary" in query else "id"
        q.order_by = OrderNode(column=ob_col, direction="DESC")
        q.limit = 1
        
    # 6. Basic Conditions using spaCy NER and dependency-like proximity rules
    if nlp is not None:
        doc = nlp(raw_query)
        for ent in doc.ents:
            if ent.label_ == "CARDINAL":
                try:
                    val = int(ent.text.replace(",", ""))
                except ValueError:
                    continue
                
                start_tok = max(0, ent.start - 5)
                prefix_tokens = [t.text.lower() for t in doc[start_tok:ent.start]]
                prefix_text = " ".join(prefix_tokens)
                
                operator = "="
                if "at least" in prefix_text or "greater than or equal" in prefix_text:
                    operator = ">="
                elif "at most" in prefix_text or "less than or equal" in prefix_text:
                    operator = "<="
                elif "not equal" in prefix_text or "different" in prefix_text or "!=" in prefix_text:
                    operator = "!="
                elif any(w in prefix_tokens for w in ["greater", "more", "higher", "above", "over"]):
                    operator = ">"
                elif any(w in prefix_tokens for w in ["less", "fewer", "smaller", "under", "below"]):
                    operator = "<"

                col_to_use = None
                for col in schema.get(q.table, []):
                    if col in prefix_text:
                        col_to_use = col
                        break
                        
                if not col_to_use:
                    if "department" in prefix_text:
                        col_to_use = "department_id"
                    else:
                        col_to_use = "salary" if val > 1000 and "salary" in schema.get(q.table, []) else ("department_id" if q.table == "employees" else "id")
                        
                q.conditions.append(ConditionNode(column=col_to_use, operator=operator, value=val))
    else:
        match = re.search(r'(department|id)[^\d]+(\d+)', query)
        if match:
            val = int(match.group(2))
            col = "department_id" if q.table == "employees" else "id"
            q.conditions.append(ConditionNode(column=col, operator="=", value=val))
        
    # 7. Joins
    if len(tables_found) > 1:
        if set(["employees", "departments"]).issubset(set(tables_found)):
            q.joins.append(JoinNode(table="departments", join_type="INNER", on_left="department_id", on_right="id"))
            if q.columns == ["*"] or "name" in q.columns:
                expanded = ["employees.name", "departments.name as dept_name"]
                q.columns = [c for c in q.columns if c != "name" and c != "*"] + expanded
                if "name" in q.group_by:
                    q.group_by = [g for g in q.group_by if g != "name"] + ["employees.name", "departments.name"]
        
    return q
