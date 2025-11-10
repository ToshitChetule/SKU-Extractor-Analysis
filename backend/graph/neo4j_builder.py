from neo4j import GraphDatabase
import pandas as pd

class Neo4jBuilder:
    def __init__(self,
                 uri="bolt://localhost:7687",
                 user="neo4j",
                 password="admin123"):
        """Initialize Neo4j connection."""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """Close Neo4j driver."""
        self.driver.close()

    def clear_database(self):
        """Optional: Clears all nodes & relationships."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def add_attribute_value_pairs(self, attributes_dict):
        """
        Add extracted attributes and values (dict format) to the graph.
        Example: {"Billing": {"Monthly", "On-Demand"}}
        """
        with self.driver.session() as session:
            for attribute, values in attributes_dict.items():
                for value in values:
                    if not attribute or not value:
                        continue
                    session.run("""
                        MERGE (a:Attribute {name: $attribute})
                        MERGE (v:Value {value: $value})
                        MERGE (a)-[:HAS_VALUE]->(v)
                    """, attribute=attribute.strip(), value=value.strip())

    def add_from_dataframe(self, df):
        """
        Add data from a DataFrame (Attribute | Value1 | Value2 ...)
        """
        with self.driver.session() as session:
            for _, row in df.iterrows():
                attribute = str(row["Attribute"]).strip()
                values = [str(v).strip() for v in row[1:] if str(v).strip()]
                for val in values:
                    session.run("""
                        MERGE (a:Attribute {name: $attribute})
                        MERGE (v:Value {value: $val})
                        MERGE (a)-[:HAS_VALUE]->(v)
                    """, attribute=attribute, val=val)
        print("✅ Data successfully pushed to Neo4j graph.")

        
    def rename_attribute(self, old_name, new_name):
        """
        Renames an existing Attribute node while preserving its relationships.
        If new_name already exists, merges both.
        """
        with self.driver.session() as session:
            session.run("""
                MATCH (a:Attribute {name: $old_name})
                WITH a
                MERGE (b:Attribute {name: $new_name})
                WITH a, b
                CALL apoc.refactor.mergeNodes([a, b]) YIELD node
                RETURN node
            """, old_name=old_name, new_name=new_name)
        print(f"✅ Renamed attribute '{old_name}' → '{new_name}' in Neo4j.")
