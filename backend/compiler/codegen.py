from .ir import IROp, ScanOp, JoinOp, FilterOp, ProjectOp, SortLimitOp, AggregateOp
import json

def generate_code(ir_node: IROp, dialect: str = "sqlite", is_grouping: bool = False, group_by_cols: list = None) -> str:
    if dialect.lower() == "mongodb":
        return generate_mongodb(ir_node)
    
    # First pass: identify tables and joins
    tables = []
    joins = []
    
    def find_tables(n):
        if isinstance(n, ScanOp): tables.append(n.table)
        elif isinstance(n, JoinOp): 
             joins.append((n.child_right.table, n.on_left, n.on_right))
             find_tables(n.child_left)
        elif hasattr(n, 'child'): find_tables(n.child)
        
    find_tables(ir_node)
    
    base_table = tables[0] if tables else ""
    has_joins = len(joins) > 0
    
    def qualify(col):
        if not has_joins or not base_table: return col
        if "." in col or "(" in col: return col
        if col == "*": return f"{base_table}.*"
        return f"{base_table}.{col}"
        
    def quote(col):
        if dialect.lower() == "mysql":
            if "." in col:
                t, c = col.split(".", 1)
                return f"`{t}`.`{c}`" if c != "*" else f"`{t}`.*"
            if "(" in col: return col
            if col == "*": return "*"
            return f"`{col}`"
        return col

    selects = []
    wheres = []
    order = ""
    limit = ""
    group_by = group_by_cols or []
    having = []
    
    def gather(n):
        nonlocal order, limit, group_by, having
        if isinstance(n, ProjectOp):
            selects.extend([quote(qualify(c)) for c in n.columns])
            gather(n.child)
        elif isinstance(n, AggregateOp):
            group_by = n.group_by
            if hasattr(n, 'having'):
                having.extend([f"{quote(qualify(c.column))} {c.operator} {c.value}" for c in n.having])
            gather(n.child)
        elif isinstance(n, SortLimitOp):
            if n.order_by:
                order = f"ORDER BY {quote(qualify(n.order_by[0]))} {n.order_by[1]}"
            if n.limit:
                limit = f"LIMIT {n.limit}"
            gather(n.child)
        elif isinstance(n, FilterOp):
            val = f"'{n.value}'" if isinstance(n.value, str) else str(n.value)
            wheres.append(f"{quote(qualify(n.column))} {n.operator} {val}")
            gather(n.child)
        elif hasattr(n, 'child') and not isinstance(n, JoinOp):
            gather(n.child)
        elif isinstance(n, JoinOp):
            gather(n.child_left)
            
    gather(ir_node)
    
    if not selects: selects = ["*"]
    
    tbl_name = quote(base_table)
    sql = f"SELECT {', '.join(selects)} FROM {tbl_name}"
    
    for t_right, col_left, col_right in joins:
        sql += f" JOIN {quote(t_right)} ON {quote(qualify(col_left))} = {quote(t_right)}.{quote(col_right)}"
        
    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
        
    if group_by:
         sql += " GROUP BY " + ", ".join([quote(qualify(c)) for c in group_by])
         
    if having:
         sql += " HAVING " + " AND ".join(having)
        
    if order: sql += f" {order}"
    if limit: sql += f" {limit}"
        
    return sql.strip() + ";"

def generate_mongodb(ir_node: IROp) -> str:
    pipeline = []
    base_table = ""
    
    def gather(n):
        nonlocal base_table
        if isinstance(n, ScanOp):
            base_table = n.table
        elif isinstance(n, FilterOp):
            gather(n.child)
            op_map = {">": "$gt", "<": "$lt", ">=": "$gte", "<=": "$lte", "!=": "$ne", "=": "$eq"}
            m_op = op_map.get(n.operator, "$eq")
            col = n.column.split(".")[-1]
            pipeline.append({"$match": {col: {m_op: n.value}}})
        elif isinstance(n, JoinOp):
            gather(n.child_left)
            pipeline.append({
                "$lookup": {
                    "from": n.child_right.table,
                    "localField": n.on_left,
                    "foreignField": n.on_right,
                    "as": n.child_right.table
                }
            })
            pipeline.append({"$unwind": f"${n.child_right.table}"})
        elif isinstance(n, SortLimitOp):
            gather(n.child)
            if n.order_by:
                pipeline.append({"$sort": {n.order_by[0]: 1 if n.order_by[1].upper() == "ASC" else -1}})
            if n.limit:
                pipeline.append({"$limit": n.limit})
        elif isinstance(n, AggregateOp):
            gather(n.child)
            group_stage = {"_id": {}}
            for g in n.group_by:
                group_stage["_id"][g] = f"${g}"
            pipeline.append({"$group": group_stage})
        elif isinstance(n, ProjectOp):
            gather(n.child)
            if n.columns != ["*"]:
                proj = {"_id": 0}
                for c in n.columns:
                    clean = c.split(".")[-1].replace("COUNT(", "").replace(")", "").replace("AVG(", "")
                    proj[clean] = 1
                pipeline.append({"$project": proj})
        elif hasattr(n, 'child'):
            gather(n.child)
            
    gather(ir_node)
    
    res = {
        "db_collection": base_table,
        "pipeline": pipeline
    }
    return json.dumps(res, indent=2)
