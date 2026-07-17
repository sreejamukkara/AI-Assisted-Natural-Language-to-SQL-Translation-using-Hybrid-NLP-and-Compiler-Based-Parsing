from .ir import IROp, ScanOp, JoinOp, FilterOp, ProjectOp, SortLimitOp, AggregateOp

def eval_binop(val):
    if not hasattr(val, "operator"):
        return val
    left = eval_binop(val.left)
    right = eval_binop(val.right)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if val.operator == '+': return left + right
        if val.operator == '-': return left - right
        if val.operator == '*': return left * right
        if val.operator == '/': return left / right if right != 0 else left
    return val

def optimize_ir(ir_node: IROp) -> tuple[IROp, list[str]]:
    """
    Simplistic Optimizer performing Predicate Pushdown, Constant Folding, and Dead Code Elimination.
    """
    stats = []
    
    def walk(node: IROp, pending_filters: list[FilterOp]) -> IROp:
        if isinstance(node, ProjectOp):
            node.child = walk(node.child, pending_filters)
            return node
            
        elif isinstance(node, SortLimitOp):
            node.child = walk(node.child, pending_filters)
            return node
            
        elif isinstance(node, AggregateOp):
            node.child = walk(node.child, pending_filters)
            return node
            
        elif isinstance(node, FilterOp):
            # Constant Folding
            old_val_str = str(node.value) if not hasattr(node.value, "operator") else f"{node.value.left} {node.value.operator} {node.value.right}"
            node.value = eval_binop(node.value)
            if not hasattr(node.value, "operator") and str(node.value) != old_val_str:
                 stats.append(f"Constant Folding: reduced {old_val_str} to {node.value}")
                 
            pending_filters.append(node)
            return walk(node.child, pending_filters)
            
        elif isinstance(node, JoinOp):
            # Dead code elimination for pending_filters before pushdown
            unique_filters = {}
            for f in pending_filters:
                key = (f.column, f.operator)
                if key in unique_filters:
                    old_f = unique_filters[key]
                    if f.operator == '>' and isinstance(f.value, (int, float)) and isinstance(old_f.value, (int, float)):
                        old_f.value = max(old_f.value, f.value)
                        stats.append(f"Dead Code Elimination: merged {f.column} > filters")
                        continue
                    elif f.operator == '<' and isinstance(f.value, (int, float)) and isinstance(old_f.value, (int, float)):
                        old_f.value = min(old_f.value, f.value)
                        stats.append(f"Dead Code Elimination: merged {f.column} < filters")
                        continue
                unique_filters[key] = f
            pending_filters = list(unique_filters.values())
        
            left_filters = []
            right_filters = []
            remaining_filters = []
            
            for f in pending_filters:
                 if "." in f.column:
                     tbl = f.column.split(".")[0]
                     if tbl == getattr(node.child_left, "table", ""):
                         left_filters.append(f)
                         stats.append(f"Pushdown filter '{f.column}' to left scan")
                     elif tbl == getattr(node.child_right, "table", ""):
                         right_filters.append(f)
                         stats.append(f"Pushdown filter '{f.column}' to right scan")
                     else:
                         remaining_filters.append(f)
                 else:
                     left_filters.append(f)
                     stats.append(f"Pushdown filter '{f.column}' to base table scan")
                     
            node.child_left = walk(node.child_left, left_filters)
            node.child_right = walk(node.child_right, right_filters)
            
            current = node
            for f in remaining_filters:
                f.child = current
                current = f
            return current
            
        elif isinstance(node, ScanOp):
            # Dead code elimination for scan level as well
            unique_filters = {}
            for f in pending_filters:
                key = (f.column, f.operator)
                if key in unique_filters:
                    old_f = unique_filters[key]
                    if f.operator == '>' and isinstance(f.value, (int, float)) and isinstance(old_f.value, (int, float)):
                        old_f.value = max(old_f.value, f.value)
                        stats.append(f"Dead Code Elimination: merged {f.column} > filters")
                        continue
                    elif f.operator == '<' and isinstance(f.value, (int, float)) and isinstance(old_f.value, (int, float)):
                        old_f.value = min(old_f.value, f.value)
                        stats.append(f"Dead Code Elimination: merged {f.column} < filters")
                        continue
                unique_filters[key] = f
            pending_filters = list(unique_filters.values())

            current = node
            for f in pending_filters:
                new_f = FilterOp(child=current, column=f.column, operator=f.operator, value=f.value)
                current = new_f
            return current
            
        return node
        
    optimized_ir = walk(ir_node, [])
    if not stats:
        stats.append("No optimizations applied")
        
    return optimized_ir, stats
