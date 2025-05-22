def format_query(query: str) -> str:
    """
    Formats the SQL query into multiple lines for better readability while preserving the case of column and table names.
    """
    segments = []
    if "SELECT" in query.upper():
        segments.append("SELECT")
        select_clause = query.split("SELECT")[1].split("FROM")[0].strip()
        segments.append(select_clause)
    if "FROM" in query.upper():
        segments.append("FROM")
        from_clause = query.split("FROM")[1].split("WHERE")[0].strip()
        segments.append(from_clause)
    if "WHERE" in query.upper():
        segments.append("WHERE")
        where_clause = query.split("WHERE")[1].strip()
        segments.append(where_clause)
    if "GROUP BY" in query.upper():
        segments.append("GROUP BY")
        group_by_clause = query.split("GROUP BY")[1].strip()
        segments.append(group_by_clause)
    if "ORDER BY" in query.upper():
        segments.append("ORDER BY")
        order_by_clause = query.split("ORDER BY")[1].strip()
        segments.append(order_by_clause)

    formatted_query = "\n".join(segments)
    return formatted_query