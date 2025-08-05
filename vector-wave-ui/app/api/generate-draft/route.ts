import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    console.log('Proxy received body:', body);
    
    // Transform data to match backend expectations
    const backendPayload = {
      content: {
        title: body.topic_title,
        content_type: body.content_type || "STANDARD",
        platform: body.platform || "LinkedIn",
        content_ownership: body.content_ownership || "EXTERNAL"
      },
      research_data: body.skip_research ? null : undefined
    };
    
    console.log('Transformed payload:', backendPayload);
    
    // Forward request to new CrewAI backend
    const response = await fetch('http://localhost:8003/api/generate-draft', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(backendPayload),
    });
    
    if (!response.ok) {
      const error = await response.text();
      return new Response(error, { 
        status: response.status,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    const data = await response.json();
    return Response.json(data);
    
  } catch (error) {
    console.error('Generate draft proxy error:', error);
    return new Response(
      JSON.stringify({ 
        error: 'Failed to generate draft',
        detail: error instanceof Error ? error.message : 'Unknown error'
      }), 
      { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}