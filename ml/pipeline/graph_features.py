"""
Builds the relationship graph using NetworkX and extracts graph features.

Nodes: Customers, Devices, IPs, Payment Instruments
Edges: "uses" or "connects_from"
"""
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import os

def build_graph(data_dir):
    """
    Reads the mapping CSVs and builds a NetworkX graph.
    """
    print("🕸️ Building the network graph...")
    G = nx.Graph()

    # Load mapping tables
    device_map = pd.read_csv(os.path.join(data_dir, "customer_device_map.csv"))
    ip_map = pd.read_csv(os.path.join(data_dir, "customer_ip_map.csv"))
    payment_map = pd.read_csv(os.path.join(data_dir, "customer_payment_map.csv"))
    
    # We also need labels to color our visualization
    labels = pd.read_csv(os.path.join(data_dir, "labels.csv"))
    ring_members = set(labels[labels["is_ring_member"] == 1]["customer_id"])

    # 1. Add Device edges
    for _, row in device_map.iterrows():
        cust = row["customer_id"]
        dev = row["device_id"]
        # Add nodes with types so we can distinguish them later
        is_fraud = cust in ring_members
        G.add_node(cust, type="customer", is_fraud=is_fraud)
        G.add_node(dev, type="device")
        G.add_edge(cust, dev)

    # 2. Add IP edges
    for _, row in ip_map.iterrows():
        cust = row["customer_id"]
        ip = row["ip_id"]
        is_fraud = cust in ring_members
        G.add_node(cust, type="customer", is_fraud=is_fraud)
        G.add_node(ip, type="ip")
        G.add_edge(cust, ip)

    # 3. Add Payment edges
    for _, row in payment_map.iterrows():
        cust = row["customer_id"]
        pay = row["payment_id"]
        is_fraud = cust in ring_members
        G.add_node(cust, type="customer", is_fraud=is_fraud)
        G.add_node(pay, type="payment")
        G.add_edge(cust, pay)

    print(f"✅ Graph built! Nodes: {G.number_of_nodes()} | Edges: {G.number_of_edges()}")
    return G


def extract_graph_features(G, refund_rate_lookup=None):
    """
    Extract 3 graph features for each CUSTOMER node.
    
    Feature 1: graph_degree
        How many total connections does this customer have?
        More connections = more entities shared = more suspicious.
    
    Feature 2: graph_component_size
        How big is the cluster this customer belongs to?
        A normal person's cluster = 3 nodes (themselves + their device + their IP).
        A ring member's cluster = 20+ nodes (all ring members + shared devices/IPs/cards).
    
    Feature 3: graph_avg_neighbor_refund_rate
        What's the average refund rate of OTHER customers connected to this customer?
        If your neighbors are all high-refund accounts, you're probably in a ring.
    """
    print("📊 Extracting graph features for each customer...")
    
    # Get all customer nodes
    customer_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "customer"]
    
    # Precompute connected components
    component_map = {}
    for component in nx.connected_components(G):
        comp_size = len(component)
        for node in component:
            component_map[node] = comp_size
    
    graph_features = []
    
    for cust in customer_nodes:
        # Feature 1: Degree (number of connections)
        degree = G.degree(cust)
        
        # Feature 2: Component size (cluster size)
        comp_size = component_map.get(cust, 1)
        
        # Feature 3: Average neighbor refund rate
        # Find all other CUSTOMER nodes in same cluster reachable through shared entities
        neighbor_refund_rates = []
        for neighbor in G.neighbors(cust):
            # neighbor is a device/IP/card node, look at ITS other customer neighbors
            for second_hop in G.neighbors(neighbor):
                if second_hop != cust and G.nodes[second_hop].get("type") == "customer":
                    if refund_rate_lookup and second_hop in refund_rate_lookup:
                        neighbor_refund_rates.append(refund_rate_lookup[second_hop])
        
        avg_neighbor_refund = np.mean(neighbor_refund_rates) if neighbor_refund_rates else 0.0
        
        graph_features.append({
            "customer_id": cust,
            "graph_degree": degree,
            "graph_component_size": comp_size,
            "graph_avg_neighbor_refund_rate": round(avg_neighbor_refund, 4),
        })
    
    result = pd.DataFrame(graph_features)
    print(f"✅ Graph features extracted for {len(result)} customers")
    return result


def add_graph_features_to_splits(data_dir, processed_dir):
    """
    Build graph, extract features, and merge them into the existing 
    feature matrix (train/val/test CSVs).
    """
    print("=" * 60)
    print("🕸️ Graph Feature Extraction Pipeline")
    print("=" * 60)
    
    # Step 1: Build the graph
    G = build_graph(data_dir)
    
    # Step 2: Load refund rates from feature matrix (needed for neighbor refund rate)
    feature_matrix = pd.read_csv(os.path.join(processed_dir, "feature_matrix.csv"))
    refund_rate_lookup = dict(zip(feature_matrix["customer_id"], feature_matrix["refund_rate"]))
    
    # Step 3: Extract graph features
    graph_df = extract_graph_features(G, refund_rate_lookup)
    
    # Step 4: Merge into all splits
    for split_name in ["feature_matrix", "train", "validation", "test"]:
        filepath = os.path.join(processed_dir, f"{split_name}.csv")
        if os.path.exists(filepath):
            split_df = pd.read_csv(filepath)
            
            # Drop old graph columns if they exist (in case of re-run)
            for col in ["graph_degree", "graph_component_size", "graph_avg_neighbor_refund_rate"]:
                if col in split_df.columns:
                    split_df = split_df.drop(columns=[col])
            
            # Merge new graph features
            split_df = split_df.merge(graph_df, on="customer_id", how="left")
            split_df["graph_degree"] = split_df["graph_degree"].fillna(0)
            split_df["graph_component_size"] = split_df["graph_component_size"].fillna(1)
            split_df["graph_avg_neighbor_refund_rate"] = split_df["graph_avg_neighbor_refund_rate"].fillna(0)
            
            split_df.to_csv(filepath, index=False)
            print(f"   ✅ {split_name}.csv updated with graph features ({len(split_df)} rows)")
    
    print("\n" + "=" * 60)
    print("✅ Graph features merged into all data splits!")
    print("=" * 60)


def test_graph_visualization():
    """Builds the graph and visualizes a small piece of it."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
    G = build_graph(data_dir)
    
    # Find all disconnected clusters (components)
    components = list(nx.connected_components(G))
    print(f"🔍 Found {len(components)} separate disconnected clusters in the data.")
    
    # Let's find a medium-sized cluster to visualize (e.g., between 10 and 30 nodes)
    target_cluster = None
    for comp in components:
        if 10 <= len(comp) <= 30:
            target_cluster = comp
            break
            
    if target_cluster:
        subgraph = G.subgraph(target_cluster)
        
        color_map = []
        for node in subgraph.nodes():
            node_type = subgraph.nodes[node]['type']
            if node_type == 'customer':
                if subgraph.nodes[node]['is_fraud']:
                    color_map.append('red')
                else:
                    color_map.append('blue')
            else:
                color_map.append('lightgray')

        plt.figure(figsize=(10, 8))
        plt.title(f"Visualizing a Cluster of size {len(target_cluster)}")
        pos = nx.spring_layout(subgraph, seed=42)
        nx.draw(subgraph, pos, node_color=color_map, with_labels=True, 
                node_size=500, font_size=8, font_color='black')
        
        output_file = "sample_graph_cluster.png"
        plt.savefig(output_file)
        print(f"📸 Saved a picture of this cluster to {output_file}")
    else:
        print("Couldn't find a medium-sized cluster to visualize.")


if __name__ == "__main__":
    import numpy as np
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
    processed_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")
    
    # Check if feature matrix exists (run feature_engineering.py first if not)
    fm_path = os.path.join(processed_dir, "feature_matrix.csv")
    if os.path.exists(fm_path):
        add_graph_features_to_splits(data_dir, processed_dir)
    else:
        print("⚠️  feature_matrix.csv not found!")
        print("   Run 'python -m ml_pipeline.feature_engineering' first, then re-run this.")
        print("\n   Falling back to visualization-only mode...")
        test_graph_visualization()
