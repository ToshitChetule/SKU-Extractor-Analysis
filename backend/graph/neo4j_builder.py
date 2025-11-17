# from neo4j import GraphDatabase
# import pandas as pd


# class Neo4jBuilder:
#     def __init__(self,
#                  uri="bolt://localhost:7687",
#                  user="neo4j",
#                  password="admin123"):
#         """Initialize Neo4j connection."""
#         self.driver = GraphDatabase.driver(uri, auth=(user, password))

#     def close(self):
#         """Close Neo4j driver."""
#         self.driver.close()

#     def clear_database(self):
#         with self.driver.session() as session:
#             session.run("MATCH (n) DETACH DELETE n")
#         print("🧹 Neo4j database cleared.")

#     # ===============================================================
#     # 🔥 NEW — CLEAR ONLY ATTRIBUTE + VALUE GRAPH (not Word nodes)
#     # ===============================================================
#     def clear_attribute_value_graph(self):
#         """
#         Clears only Attribute and Value nodes.
#         DOES NOT remove Word nodes.
#         """
#         with self.driver.session() as session:
#             session.run("""
#                 MATCH (a:Attribute) DETACH DELETE a;
#                 MATCH (v:Value) DETACH DELETE v;
#             """)
#         print("🧹 Cleared Attribute & Value graph (Word nodes preserved).")




#     def get_value_attribute_map(self):
#         with self.driver.session() as session:
#             result = session.run("""
#                 MATCH (a:Attribute)-[:HAS_VALUE]->(v:Value)
#                 RETURN v.value AS value, collect(a.name) AS attributes
#             """)
#             return {record["value"]: record["attributes"] for record in result}



#     # ===============================================================
#     # 🔥 NEW — INSERT VOCABULARY WORDS INTO KG
#     # ===============================================================
   
#     def insert_vocabulary(self, vocab):
#         """Insert vocab into Neo4j safely even if nested lists exist."""
#         flat_words = set()

#         def flatten(x):
#             if isinstance(x, str):
#                 flat_words.add(x.strip())
#             elif isinstance(x, (list, tuple, set)):
#                 for item in x:
#                     flatten(item)
#             else:
#                 flat_words.add(str(x).strip())

#         flatten(vocab)

#         with self.driver.session() as session:
#             for w in flat_words:
#                 if w:  # skip empty
#                     session.run("MERGE (:Word {text: $w})", w=w)

#         print(f"🌐 Inserted {len(flat_words)} words into KG.")

#         def get_all_values(self):
#             """
#             Return a list of all distinct Value.value strings present in the graph.
#             """
#             with self.driver.session() as session:
#                 result = session.run("""
#                     MATCH (v:Value)
#                     RETURN DISTINCT v.value AS value
#                 """)
#                 return [record["value"] for record in result]



#     def get_all_words(self):
#         with self.driver.session() as session:
#             result = session.run("MATCH (w:Word) RETURN w.text AS word")
#             return [r["word"] for r in result]

    
#         # ===============================================================
#     # NEW — Insert Attribute → Value pairs after LLaMA extraction
#     # ===============================================================
#     def add_attribute_value_pairs(self, attr_map):
#         """
#         attr_map example:
#         {
#             "Product family": {"Synexa"},
#             "Edition": {"Enterprise", "Basic"}
#         }
#         """
#         with self.driver.session() as session:
#             for attr, values in attr_map.items():

#                 # Merge Attribute node
#                 session.run("""
#                     MERGE (a:Attribute {name: $attr})
#                 """, attr=attr)

#                 # Merge each Value node + relation
#                 for value in values:
#                     session.run("""
#                         MERGE (a:Attribute {name: $attr})
#                         MERGE (v:Value {value: $value})
#                         MERGE (a)-[:HAS_VALUE]->(v)
#                     """, attr=attr, value=value)

#         print("✅ Added Attribute–Value pairs to KG.")



#     # ===============================================================
#     # 🔄 RENAME ATTRIBUTE
#     # ===============================================================
#     def rename_attribute(self, old_name, new_name):
#         """
#         Safely renames an Attribute node while keeping all HAS_VALUE relationships.
#         Case-insensitive and safe.
#         """
#         with self.driver.session() as session:
#             # Copy relationships
#             session.run("""
#                 MATCH (a:Attribute)
#                 WHERE toLower(a.name) = toLower($old_name)
#                 OPTIONAL MATCH (a)-[:HAS_VALUE]->(v)
#                 WITH a, COLLECT(DISTINCT v) AS vals
#                 MERGE (b:Attribute {name: $new_name})
#                 WITH a, b, vals
#                 UNWIND vals AS val
#                 MERGE (b)-[:HAS_VALUE]->(val)
#             """, old_name=old_name, new_name=new_name)

#             # Delete old node
#             session.run("""
#                 MATCH (a:Attribute)
#                 WHERE toLower(a.name) = toLower($old_name)
#                 DETACH DELETE a
#             """, old_name=old_name)

#         print(f"✅ Renamed attribute '{old_name}' → '{new_name}'")

#     # ===============================================================
#     # 🗑️ DELETE ATTRIBUTE
#     # ===============================================================
#     def delete_attribute(self, attr_name, cleanup_orphans=True):
#         """Deletes an attribute and optionally removes orphaned values."""
#         with self.driver.session() as session:
#             session.run("""
#                 MATCH (a:Attribute)-[:HAS_VALUE]->(v:Value)
#                 WHERE toLower(a.name) = toLower($attr_name)
#                 WITH a, collect(v) AS vals
#                 DETACH DELETE a
#                 WITH vals
#                 UNWIND vals AS v
#                 OPTIONAL MATCH (x)-[:HAS_VALUE]->(v)
#                 WITH v, COUNT(x) AS refs
#                 WHERE refs = 0
#                 DELETE v
#             """, attr_name=attr_name)
#         print(f"🗑️ Deleted attribute '{attr_name}' and cleaned orphan values.")

#     # ===============================================================
#     # 🔧 ADD VALUE UNDER ATTRIBUTE
#     # ===============================================================
#     def add_value(self, attr_name, new_value):
#         """Adds a new value under an attribute."""
#         with self.driver.session() as session:
#             session.run("""
#                 MERGE (a:Attribute {name: $attr_name})
#                 MERGE (v:Value {value: $new_value})
#                 MERGE (a)-[:HAS_VALUE]->(v)
#             """, attr_name=attr_name.strip(), new_value=new_value.strip())
#         print(f"➕ Added value '{new_value}' under '{attr_name}'")

#     # ===============================================================
#     # 🗑️ REMOVE VALUE
#     # ===============================================================
#     def remove_value(self, attr_name, value_name):
#         """Removes value from attribute and cleans orphans."""
#         with self.driver.session() as session:
#             # Remove relationship
#             session.run("""
#                 MATCH (a:Attribute)-[r:HAS_VALUE]->(v:Value)
#                 WHERE toLower(a.name) = toLower($attr_name)
#                   AND toLower(v.value) = toLower($value_name)
#                 DELETE r
#             """, attr_name=attr_name, value_name=value_name)

#             # Clean orphan values
#             session.run("""
#                 MATCH (v:Value)
#                 WHERE toLower(v.value) = toLower($value_name)
#                   AND NOT (()-[:HAS_VALUE]->(v))
#                 DELETE v
#             """, value_name=value_name)

#         print(f"🗑️ Removed value '{value_name}' from '{attr_name}'")

#     # ===============================================================
#     # 🔄 RENAME VALUE
#     # ===============================================================
#     def rename_value(self, attr_name, old_value, new_value):
#         """Safely renames a Value under a specific attribute."""
#         with self.driver.session() as session:
#             session.run("""
#                 MATCH (a:Attribute)-[r:HAS_VALUE]->(v:Value)
#                 WHERE toLower(a.name) = toLower($attr_name)
#                   AND toLower(v.value) = toLower($old_value)
#                 MERGE (v2:Value {value: $new_value})
#                 MERGE (a)-[:HAS_VALUE]->(v2)
#                 DELETE r
#                 WITH v
#                 OPTIONAL MATCH (x)-[:HAS_VALUE]->(v)
#                 WITH v, COUNT(x) AS refs
#                 WHERE refs = 0
#                 DELETE v
#             """, attr_name=attr_name, old_value=old_value, new_value=new_value)

#         print(f"🔁 Renamed value '{old_value}' → '{new_value}' under '{attr_name}'")

#     # ===============================================================
#     # 📥 GET VALUES UNDER ATTRIBUTE
#     # ===============================================================

#     def get_values(self, attr_name):
#         with self.driver.session() as session:
#             result = session.run("""
#                 MATCH (a:Attribute)-[:HAS_VALUE]->(v:Value)
#                 WHERE toLower(a.name) = toLower($attr_name)
#                 RETURN DISTINCT v.value AS value
#             """, attr_name=attr_name)
#             return [record["value"] for record in result]

#     def get_all_values(self):    # <-- MUST BE HERE, SAME LEVEL
#         """
#         Return a list of all distinct Value.value strings present in the graph.
#         """
#         with self.driver.session() as session:
#             result = session.run("""
#                 MATCH (v:Value)
#                 RETURN DISTINCT v.value AS value
#             """)
#             return [record["value"] for record in result]



#     # ===============================================================
#     # 🔗 MERGE MULTIPLE ATTRIBUTES
#     # ===============================================================
#     def merge_attributes(self, attr_list, new_name):
#         """Merges multiple attributes into one."""
#         with self.driver.session() as session:
#             session.run("""
#                 MATCH (a:Attribute)
#                 WHERE toLower(a.name) IN [x IN $attr_list | toLower(x)]
#                 OPTIONAL MATCH (a)-[:HAS_VALUE]->(v)
#                 WITH COLLECT(DISTINCT v) AS allVals, COLLECT(DISTINCT a) AS oldAttrs
#                 MERGE (b:Attribute {name: $new_name})
#                 FOREACH (v IN allVals | MERGE (b)-[:HAS_VALUE]->(v))
#                 FOREACH (x IN oldAttrs | DETACH DELETE x)
#             """, attr_list=attr_list, new_name=new_name)

#         print(f"🔗 Merged {attr_list} → '{new_name}'")



# backend/graph/neo4j_builder.py
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
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("🧹 Neo4j database cleared.")

    # ===============================================================
    # 🔥 NEW — CLEAR ONLY ATTRIBUTE + VALUE GRAPH (not Word nodes)
    # ===============================================================
    def clear_attribute_value_graph(self):
        """
        Clears only Attribute and Value nodes.
        DOES NOT remove Word nodes.
        """
        with self.driver.session() as session:
            session.run("""
                MATCH (a:Attribute) DETACH DELETE a;
                MATCH (v:Value) DETACH DELETE v;
            """)
        print("🧹 Cleared Attribute & Value graph (Word nodes preserved).")

    # ===============================================================
    # 🔥 NEW — INSERT VOCABULARY WORDS INTO KG
    # ===============================================================
    def insert_vocabulary(self, vocab):
        """Insert vocab into Neo4j safely even if nested lists exist."""
        flat_words = set()

        def flatten(x):
            if isinstance(x, str):
                flat_words.add(x.strip())
            elif isinstance(x, (list, tuple, set)):
                for item in x:
                    flatten(item)
            else:
                flat_words.add(str(x).strip())

        flatten(vocab)

        with self.driver.session() as session:
            for w in flat_words:
                if w:  # skip empty
                    session.run("MERGE (:Word {text: $w})", w=w)

        print(f"🌐 Inserted {len(flat_words)} words into KG.")

    # ===============================================================
    # 📥 GET WORDS
    # ===============================================================
    def get_all_words(self):
        with self.driver.session() as session:
            result = session.run("MATCH (w:Word) RETURN w.text AS word")
            return [r["word"] for r in result]

    # ===============================================================
    # 📥 GET VALUES (flat list)
    # ===============================================================
    def get_all_values(self):
        """
        Return a list of all distinct Value.value strings present in the graph.
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (v:Value)
                RETURN DISTINCT v.value AS value
            """)
            return [record["value"] for record in result]

    # ===============================================================
    # 📥 GET VALUE -> ATTRIBUTE(S) MAP
    # ===============================================================
    def get_value_attribute_map(self):
        """
        Returns a dict: { value_string : [attributeName1, attributeName2, ...] }
        If a value is linked to multiple attributes, all attribute names are returned.
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Attribute)-[:HAS_VALUE]->(v:Value)
                RETURN v.value AS value, collect(DISTINCT a.name) AS attributes
            """)
            return {record["value"]: record["attributes"] for record in result}

    # ===============================================================
    # NEW — Insert Attribute → Value pairs after LLaMA extraction
    # ===============================================================
    def add_attribute_value_pairs(self, attr_map):
        """
        attr_map example:
        {
            "Product family": {"Synexa"},
            "Edition": {"Enterprise", "Basic"}
        }
        """
        with self.driver.session() as session:
            for attr, values in attr_map.items():

                # Merge Attribute node
                session.run("""
                    MERGE (a:Attribute {name: $attr})
                """, attr=attr)

                # Merge each Value node + relation
                for value in values:
                    # make sure to skip empty / None
                    if value is None:
                        continue
                    vstr = str(value).strip()
                    if not vstr:
                        continue
                    session.run("""
                        MERGE (a:Attribute {name: $attr})
                        MERGE (v:Value {value: $value})
                        MERGE (a)-[:HAS_VALUE]->(v)
                    """, attr=attr, value=vstr)

        print("✅ Added Attribute–Value pairs to KG.")

    # ===============================================================
    # 🔄 RENAME ATTRIBUTE
    # ===============================================================
    def rename_attribute(self, old_name, new_name):
        """
        Safely renames an Attribute node while keeping all HAS_VALUE relationships.
        Case-insensitive and safe.
        """
        with self.driver.session() as session:
            # Copy relationships
            session.run("""
                MATCH (a:Attribute)
                WHERE toLower(a.name) = toLower($old_name)
                OPTIONAL MATCH (a)-[:HAS_VALUE]->(v)
                WITH a, COLLECT(DISTINCT v) AS vals
                MERGE (b:Attribute {name: $new_name})
                WITH a, b, vals
                UNWIND vals AS val
                MERGE (b)-[:HAS_VALUE]->(val)
            """, old_name=old_name, new_name=new_name)

            # Delete old node
            session.run("""
                MATCH (a:Attribute)
                WHERE toLower(a.name) = toLower($old_name)
                DETACH DELETE a
            """, old_name=old_name)

        print(f"✅ Renamed attribute '{old_name}' → '{new_name}'")

    # ===============================================================
    # 🗑️ DELETE ATTRIBUTE
    # ===============================================================
    def delete_attribute(self, attr_name, cleanup_orphans=True):
        """Deletes an attribute and optionally removes orphaned values."""
        with self.driver.session() as session:
            session.run("""
                MATCH (a:Attribute)-[:HAS_VALUE]->(v:Value)
                WHERE toLower(a.name) = toLower($attr_name)
                WITH a, collect(v) AS vals
                DETACH DELETE a
                WITH vals
                UNWIND vals AS v
                OPTIONAL MATCH (x)-[:HAS_VALUE]->(v)
                WITH v, COUNT(x) AS refs
                WHERE refs = 0
                DELETE v
            """, attr_name=attr_name)
        print(f"🗑️ Deleted attribute '{attr_name}' and cleaned orphan values.")

    # ===============================================================
    # 🔧 ADD VALUE UNDER ATTRIBUTE
    # ===============================================================
    def add_value(self, attr_name, new_value):
        """Adds a new value under an attribute."""
        with self.driver.session() as session:
            session.run("""
                MERGE (a:Attribute {name: $attr_name})
                MERGE (v:Value {value: $new_value})
                MERGE (a)-[:HAS_VALUE]->(v)
            """, attr_name=attr_name.strip(), new_value=new_value.strip())
        print(f"➕ Added value '{new_value}' under '{attr_name}'")

    # ===============================================================
    # 🗑️ REMOVE VALUE
    # ===============================================================
    def remove_value(self, attr_name, value_name):
        """Removes value from attribute and cleans orphans."""
        with self.driver.session() as session:
            # Remove relationship
            session.run("""
                MATCH (a:Attribute)-[r:HAS_VALUE]->(v:Value)
                WHERE toLower(a.name) = toLower($attr_name)
                  AND toLower(v.value) = toLower($value_name)
                DELETE r
            """, attr_name=attr_name, value_name=value_name)

            # Clean orphan values
            session.run("""
                MATCH (v:Value)
                WHERE toLower(v.value) = toLower($value_name)
                  AND NOT (()-[:HAS_VALUE]->(v))
                DELETE v
            """, value_name=value_name)

        print(f"🗑️ Removed value '{value_name}' from '{attr_name}'")

    # ===============================================================
    # 🔄 RENAME VALUE
    # ===============================================================
    def rename_value(self, attr_name, old_value, new_value):
        """Safely renames a Value under a specific attribute."""
        with self.driver.session() as session:
            session.run("""
                MATCH (a:Attribute)-[r:HAS_VALUE]->(v:Value)
                WHERE toLower(a.name) = toLower($attr_name)
                  AND toLower(v.value) = toLower($old_value)
                MERGE (v2:Value {value: $new_value})
                MERGE (a)-[:HAS_VALUE]->(v2)
                DELETE r
                WITH v
                OPTIONAL MATCH (x)-[:HAS_VALUE]->(v)
                WITH v, COUNT(x) AS refs
                WHERE refs = 0
                DELETE v
            """, attr_name=attr_name, old_value=old_value, new_value=new_value)

        print(f"🔁 Renamed value '{old_value}' → '{new_value}' under '{attr_name}'")

    # ===============================================================
    # 📥 GET VALUES UNDER ATTRIBUTE
    # ===============================================================
    def get_values(self, attr_name):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Attribute)-[:HAS_VALUE]->(v:Value)
                WHERE toLower(a.name) = toLower($attr_name)
                RETURN DISTINCT v.value AS value
            """, attr_name=attr_name)
            return [record["value"] for record in result]

    # ===============================================================
    # 🔗 MERGE MULTIPLE ATTRIBUTES
    # ===============================================================
    def merge_attributes(self, attr_list, new_name):
        """Merges multiple attributes into one."""
        with self.driver.session() as session:
            session.run("""
                MATCH (a:Attribute)
                WHERE toLower(a.name) IN [x IN $attr_list | toLower(x)]
                OPTIONAL MATCH (a)-[:HAS_VALUE]->(v)
                WITH COLLECT(DISTINCT v) AS allVals, COLLECT(DISTINCT a) AS oldAttrs
                MERGE (b:Attribute {name: $new_name})
                FOREACH (v IN allVals | MERGE (b)-[:HAS_VALUE]->(v))
                FOREACH (x IN oldAttrs | DETACH DELETE x)
            """, attr_list=attr_list, new_name=new_name)

        print(f"🔗 Merged {attr_list} → '{new_name}'")
