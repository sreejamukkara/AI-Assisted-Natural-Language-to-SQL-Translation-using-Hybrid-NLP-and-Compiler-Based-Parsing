from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import traceback
import sys
import os

# Add the current dir to path to find compiler/database correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.schema import init_db, get_schema, execute_query
from compiler.lexer import tokenize, LexerError
from compiler.parser import parse_to_ast, ParserError
from compiler.heuristic_parser import heuristic_nl_to_ast
from compiler.semantic import validate_ast, SemanticError
from compiler.ir import ast_to_ir, ir_to_dict
from compiler.optimizer import optimize_ir
from compiler.codegen import generate_code
from compiler.llm_integration import get_sql_from_llm
from compiler.diagnostics import CompilerException, CompilerError

app = FastAPI()

@app.on_event("startup")
def startup_event():
    init_db()

class QueryRequest(BaseModel):
    query: str
    use_llm_fallback: bool = True
    dialect: str = "sqlite"

@app.get("/api/schema")
def schema():
    return get_schema()

@app.post("/api/query")
def process_query(req: QueryRequest):
    query = req.query
    use_llm = req.use_llm_fallback
    schema = get_schema()
    
    res = {
        "steps": {
            "tokens": [],
            "ast": None,
            "semantic_validation": None,
            "ir": None,
            "optimization": None,
            "sql": None,
            "used_llm": False,
            "diagnostics": None
        },
        "result": {
            "columns": [],
            "rows": []
        }
    }
    
    try:
        # Phase 1: Lexer
        try:
            tokens = tokenize(query)
            res["steps"]["tokens"] = tokens
        except LexerError as e:
            raise CompilerError("Lexer", e.message, e.position)
            
        # Phase 2: Parser
        ast = None
        try:
             ast = parse_to_ast(query)
        except ParserError as e:
             # Fallback to Heuristic Parser
             h_ast = heuristic_nl_to_ast(query, schema)
             if h_ast:
                 ast = h_ast
             else:
                 raise CompilerError("Parser", e.message, e.position, e.suggestion)
                 
        res["steps"]["ast"] = ast.to_dict()
        
        # Phase 3: Semantic Analysis
        try:
            ast = validate_ast(ast, use_llm_fallback=use_llm)
            res["steps"]["semantic_validation"] = "Passed"
        except SemanticError as e:
            raise CompilerError("Semantic", e.message, suggestion=e.suggestion)
            
        # Phase 4: IR Generation
        ir_tree = ast_to_ir(ast)
        res["steps"]["ir"] = ir_to_dict(ir_tree)
        
        # Phase 5: Optimization
        opt_ir, stats = optimize_ir(ir_tree)
        res["steps"]["optimization"] = stats
        
        # Phase 6: Code Gen
        sql = generate_code(opt_ir, dialect=req.dialect, is_grouping=bool(ast.group_by), group_by_cols=ast.group_by)
        res["steps"]["sql"] = sql
        
        # Execute Query
        if req.dialect.lower() == "sqlite":
            db_res = execute_query(sql)
            if "error" in db_res:
                raise CompilerError("Execution", db_res["error"], suggestion="Generated SQL was invalid for SQLite")
            res["result"] = db_res
        else:
            res["result"] = {"columns": ["Info"], "rows": [[f"Execution skipped for dialect: {req.dialect}"]]}
        
    except CompilerError as ce:
        res["steps"]["diagnostics"] = ce.to_dict()
        
        # Super Fallback: Direct SQL LLM
        if use_llm:
            try:
                raw_sql = get_sql_from_llm(query, schema)
                if raw_sql and not "error" in raw_sql.lower() and "select" in raw_sql.lower():
                    res["steps"]["sql"] = raw_sql
                    res["steps"]["used_llm"] = True
                    db_res = execute_query(raw_sql)
                    if "error" not in db_res:
                         res["result"] = db_res
                         res["steps"]["diagnostics"] = {"message": "Repaired entirely using AI"}
            except Exception:
                pass
                
    except Exception as e:
        traceback.print_exc()
        res["steps"]["diagnostics"] = {"type": "Internal Error", "message": str(e)}

    return res

from pathlib import Path
frontend_dir = Path(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
