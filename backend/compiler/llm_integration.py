import os
import json
import google.generativeai as genai
from .ast_nodes import SQLQuery, ConditionNode

API_KEY = os.environ.get("GEMINI_API_KEY", "")

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    model = None

def enrich_ast_proactively(ast: SQLQuery, schema: dict, error_reason: str) -> SQLQuery:
    """
    Proactively uses LLM to patch missing or incorrect AST nodes instead of restarting from scratch.
    """
    if not model:
        return ast
        
    prompt = f"""You are a JSON AST repair tool. Output ONLY the corrected JSON object, nothing else.

    The parser constructed an incomplete/invalid AST. Please fix the entity names to match the schema strictly.
    Error Reason: {error_reason}
    
    Schema: {json.dumps(schema)}
    
    Current AST (JSON):
    {json.dumps(ast.to_dict())}
    
    Output ONLY valid JSON representing the fixed AST.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        ast.table = data.get("table", ast.table)
        if "conditions" in data:
            ast.conditions = [ConditionNode(column=c["column"], operator=c["operator"], value=c["value"]) for c in data["conditions"]]
        return ast
    except:
        return ast

def get_ast_from_llm(query: str, schema: dict) -> dict:
    if not model:
        raise ValueError("No GEMINI_API_KEY provided.")

    prompt = f"""You are a precise SQL AST generator. Never add explanation. Never wrap in markdown. Only output raw JSON.

    Convert Natural Language to JSON AST. Schema: {json.dumps(schema)}
    Query: "{query}"

    You must output ONLY valid JSON matching this exact structure:
    {{
       "operation": "SELECT",
       "table": "main_table",
       "columns": ["col1", "col2"],
       "conditions": [ {{"column": "salary", "operator": ">=", "value": 50000}} ],
       "joins": [ {{"table": "departments", "type": "INNER", "on_left": "department_id", "on_right": "id"}} ],
       "order_by": {{"column": "salary", "direction": "DESC"}}
    }}
    Omit any keys if they are not needed. Only return the JSON.
    """
    try:
        res = model.generate_content(prompt)
        text = res.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}

def get_sql_from_llm(query: str, schema: dict) -> str:
    if not model:
        raise ValueError("No GEMINI_API_KEY provided.")

    prompt = f"""You are a SQL generator. Output ONLY the raw SQL statement, no explanation, no markdown formatting.
Schema: {json.dumps(schema)}
Query: '{query}'
Return ONLY the raw SQL query."""
    try:
        res = model.generate_content(prompt)
        return res.text.replace("```sql", "").replace("```", "").strip()
    except Exception as e:
        return str(e)
