from dataclasses import dataclass
from typing import List, Any, Dict, Optional
from .ast_nodes import SQLQuery

@dataclass
class IROp:
    def to_dict(self) -> Dict:
        pass

@dataclass
class ScanOp(IROp):
    table: str
    def to_dict(self):
        return {"op": "Scan", "table": self.table}

@dataclass
class FilterOp(IROp):
    child: IROp
    column: str
    operator: str
    value: Any
    def to_dict(self):
        return {
            "op": "Filter",
            "condition": f"{self.column} {self.operator} {self.value}",
            "child": self.child.to_dict()
        }

@dataclass
class JoinOp(IROp):
    child_left: IROp
    child_right: IROp
    on_left: str
    on_right: str
    def to_dict(self):
        return {
            "op": "Join",
            "on": f"{self.on_left} = {self.on_right}",
            "left": self.child_left.to_dict(),
            "right": self.child_right.to_dict()
        }

@dataclass
class ProjectOp(IROp):
    child: IROp
    columns: List[str]
    def to_dict(self):
        return {
            "op": "Project",
            "columns": self.columns,
            "child": self.child.to_dict()
        }

@dataclass
class SortLimitOp(IROp):
    child: IROp
    order_by: Optional[tuple] # (column, direction)
    limit: Optional[int]
    def to_dict(self):
        return {
            "op": "Sort/Limit",
            "order_by": f"{self.order_by[0]} {self.order_by[1]}" if self.order_by else None,
            "limit": self.limit,
            "child": self.child.to_dict()
        }

@dataclass
class AggregateOp(IROp):
    child: IROp
    group_by: List[str]
    having: List[Any]  # list of conditions
    def to_dict(self):
        # We need to serialize having condition values properly if they have BinOps, but we can rely on stringification for IR
        return {
            "op": "Aggregate",
            "group_by": self.group_by,
            "having": [f"{c.column} {c.operator} {c.value}" for c in self.having] if self.having else [],
            "child": self.child.to_dict()
        }

def ast_to_ir(ast: SQLQuery) -> IROp:
    # Build bottom-up
    current_node = ScanOp(table=ast.table)
    
    # Joins
    for join in ast.joins:
        right_scan = ScanOp(table=join.table)
        current_node = JoinOp(child_left=current_node, child_right=right_scan, on_left=join.on_left, on_right=join.on_right)
        
    # Filters
    for cond in ast.conditions:
        current_node = FilterOp(child=current_node, column=cond.column, operator=cond.operator, value=cond.value)
        
    # Sort and Limit
    if ast.order_by or ast.limit:
        order_tuple = (ast.order_by.column, ast.order_by.direction) if ast.order_by else None
        current_node = SortLimitOp(child=current_node, order_by=order_tuple, limit=ast.limit)
        
    # Aggregate
    if ast.group_by or getattr(ast, 'having', []):
        current_node = AggregateOp(child=current_node, group_by=ast.group_by, having=getattr(ast, 'having', []))
    
    # Project (and simplistic group by handling embedded via columns containing aggregates conceptually)
    current_node = ProjectOp(child=current_node, columns=ast.columns)
    
    return current_node

def ir_to_dict(ir_tree: IROp) -> dict:
    return ir_tree.to_dict()
