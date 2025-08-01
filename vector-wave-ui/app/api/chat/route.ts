import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { message, context } = await request.json();
    
    // Forward to backend API
    const response = await fetch('http://localhost:8001/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        message,
        context: {
          ...context,
          available_folders: context.folders || []
        }
      })
    });

    if (!response.ok) {
      // Fallback to simple responses if backend is down
      return NextResponse.json({
        response: "Przepraszam, ale mój backend jest obecnie niedostępny. Mogę jednak pomóc Ci z podstawowymi pytaniami o Vector Wave. O co chciałbyś zapytać?"
      });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Chat API error:', error);
    
    // Return a natural fallback response
    return NextResponse.json({
      response: "Ups, coś poszło nie tak z połączeniem. Ale słucham - o czym chcesz pogadać? Mogę opowiedzieć o dostępnych folderach, strategii publikacji, albo o czymkolwiek innym co Cię interesuje!"
    });
  }
}