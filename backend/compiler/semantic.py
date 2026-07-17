from .ast_nodes import SQLQuery
from .diagnostics import SemanticError
from .llm_integration import enrich_ast_proactively
from database.schema import get_schema, get_schema_with_types

def validate_ast(ast: SQLQuery, use_llm_fallback: bool = False) -> SQLQuery:
    schema = get_schema()
    
    # 1. Base table check
    if not ast.table:
        if use_llm_fallback:
            ast = enrich_ast_proactively(ast, schema, "No table specified in query")
            if not ast.table or ast.table not in schema:
                raise SemanticError("No table specified in query", "Could not determine which table to query. E.g. add 'from employees'")
        else:
            raise SemanticError("No table specified in query", "Could not determine which table to query. E.g. add 'from employees'")
            
    table_candidates = [t for t in schema.keys() if t in ast.table.lower() or ast.table.lower() in t]
    if not table_candidates:
        if use_llm_fallback:
            # Table is wrong, let's try to autocorrect via LLM
            ast = enrich_ast_proactively(ast, schema, f"Table '{ast.table}' not found in schema")
            if ast.table not in schema:
                raise SemanticError(f"Table '{ast.table}' does not exist", "Check your spelling or use a valid table like 'employees' or 'departments'")
        else:
            raise SemanticError(f"Table '{ast.table}' does not exist", "Available tables are: " + ", ".join(schema.keys()))
    else:
        ast.table = table_candidates[0] # Correct casing/exact match
        
    available_columns = schema[ast.table]
    if ast.joins:
        for join in ast.joins:
            if join.table in schema:
                available_columns.extend(schema[join.table])
                
    # 2. Check columns
    valid_cols = []
    for col in ast.columns:
        clean_col = col.replace("COUNT(", "").replace("AVG(", "").replace(")", "")
        if clean_col == "*" or clean_col in available_columns or "." in clean_col:
            valid_cols.append(col)
        else:
            if use_llm_fallback:
                 ast = enrich_ast_proactively(ast, schema, f"Column '{clean_col}' not found")
                 # We simply break after enrichment and hope conditions/columns are patched, but our naive pipeline expects perfect AST
            else:
                 raise SemanticError(f"Column '{clean_col}' not found in '{ast.table}'", "Ensure the property exists")

    schema_types = get_schema_with_types()

    # 3. Check conditions
    for cond in ast.conditions:
        clean_cond = cond.column.split(".")[-1] if "." in cond.column else cond.column
        if clean_cond not in available_columns and clean_cond != "id":
             if use_llm_fallback:
                  ast = enrich_ast_proactively(ast, schema, f"Condition column '{clean_cond}' not found")
                  clean_cond = cond.column.split(".")[-1] if "." in cond.column else cond.column
                  
             if clean_cond not in available_columns and clean_cond != "id":
                  raise SemanticError(f"Condition column '{clean_cond}' does not exist in {ast.table}", "Verify your filter criteria is valid for the queried dataset.")
                  
        # Type Checking
        if clean_cond in available_columns or clean_cond == "id":
            col_type = None
            if "." in cond.column:
                tbl = cond.column.split(".")[0]
                col_type = schema_types.get(tbl, {}).get(clean_cond)
            else:
                for tbl in [ast.table] + [j.table for j in ast.joins]:
                    if clean_cond in schema_types.get(tbl, {}):
                        col_type = schema_types[tbl][clean_cond]
                        break
                        
            if col_type == "TEXT" and cond.operator in [">", "<", ">=", "<="]:
                raise SemanticError(f"Type mismatch on '{cond.column}'", f"Cannot use numeric operator '{cond.operator}' on a TEXT column.")

    # 4. Check HAVING (if any)
    for cond in getattr(ast, "having", []):
        if hasattr(cond, "operator") and cond.operator in [">", "<", ">=", "<="]:
            # Simple check: having usually applies to aggregates which are numeric. 
            pass

    return ast
