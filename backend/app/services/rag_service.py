import openai
from app.config import settings
from app.database import supabase


client = openai.OpenAI(api_key=settings.openai_api_key)


async def embed_text(text: str) -> list:
    """Convert text into a 1536-dimension vector using OpenAI."""
    response = client.embeddings.create(
        model='text-embedding-3-small',
        input=text
    )
    return response.data[0].embedding




async def lookup_faq(query: str, business_id: str) -> str:
    """
    Find the most relevant SOP chunks for a customer's question.
    Uses cosine similarity — semantically similar text scores highest.
    """
    query_vector = await embed_text(query)


    result = supabase.rpc('match_sop_chunks', {
        'query_embedding': query_vector,
        'match_business_id': business_id,
        'match_count': 3
    }).execute()


    if not result.data:
        return 'No relevant FAQ information found.'


    return '\n\n'.join([row['content'] for row in result.data])




async def ingest_sop(content: str, business_id: str):
    """
    Chunk a text document into 500-word pieces and embed each chunk.
    Call this when an owner uploads a new SOP via the /settings page.
    """
    words = content.split()
    chunk_size, overlap = 500, 50
    chunks = [
        ' '.join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size - overlap)
    ]
    for chunk in chunks:
        embedding = await embed_text(chunk)
        supabase.table('sop_chunks').insert({
            'business_id': business_id,
            'content': chunk,
            'embedding': embedding
        }).execute()

