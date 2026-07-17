from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass
class ConditionNode:
    column: str
    operator: str
    value: Any

@dataclass
class JoinNode:
    table: str
    join_type: str  # INNER, LEFT, etc.
    on_left: str
    on_right: str

@dataclass
class OrderNode:
    column: str
    direction: str  # ASC or DESC

@dataclass
class BinOpNode:
    left: Any
    operator: str
    right: Any

@dataclass
class SQLQuery:
    operation: str = "SELECT"
    table: str = ""
    columns: List[str] = field(default_factory=lambda: ["*"])
    conditions: List[ConditionNode] = field(default_factory=list)
    joins: List[JoinNode] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    having: List[ConditionNode] = field(default_factory=list)
    order_by: Optional[OrderNode] = None
    limit: Optional[int] = None

    def to_dict(self):
        def val_to_dict(val):
            if isinstance(val, BinOpNode):
                return {"type": "BinOp", "left": val_to_dict(val.left), "operator": val.operator, "right": val_to_dict(val.right)}
            return val

        return {
            "operation": self.operation,
            "table": self.table,
            "columns": self.columns,
            "conditions": [{"column": c.column, "operator": c.operator, "value": val_to_dict(c.value)} for c in self.conditions],
            "joins": [{"table": j.table, "join_type": j.join_type, "on_left": j.on_left, "on_right": j.on_right} for j in self.joins],
            "group_by": self.group_by,
            "having": [{"column": c.column, "operator": c.operator, "value": val_to_dict(c.value)} for c in getattr(self, 'having', [])],
            "order_by": {"column": self.order_by.column, "direction": self.order_by.direction} if self.order_by else None,
            "limit": self.limit
        }
