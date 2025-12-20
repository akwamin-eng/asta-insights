# storage/vector_storage.py
def update_vector_data(supabase_client, property_id, data):
    return supabase_client.table("asta_properties").update({
        "price_ghs": data['ghs'],
        "price_usd": data['usd'],
        "ai_insight": data['insight'],
        "embedding": data['embedding'],
        "economic_snapshot": data['econ']
    }).eq("id", property_id).execute()
