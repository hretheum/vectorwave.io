#!/usr/bin/env node

require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });
const { SubstackAdapter } = require('../src/adapters/substack-adapter');

async function testSubstackAdapter() {
  const adapter = new SubstackAdapter();
  
  try {
    console.log('🧪 Test Substack Adapter - Odtwarzanie sesji w automatyzacji');
    console.log('================================================\n');
    
    // Krok 1: Inicjalizacja z zapisaną sesją
    console.log('1️⃣ Inicjalizacja adaptera...');
    await adapter.initialize('personal');
    
    // Krok 2: Uruchomienie przeglądarki i przywrócenie sesji
    console.log('\n2️⃣ Uruchamianie przeglądarki i przywracanie sesji...');
    await adapter.startBrowser();
    
    // Krok 3: Test publikacji (jako draft z tagami)
    console.log('\n3️⃣ Test publikacji posta...');
    const testPost = {
      title: `Test Post - ${new Date().toLocaleString()}`,
      content: `To jest testowy post utworzony automatycznie przez Substack Adapter.\n\nCzas utworzenia: ${new Date().toISOString()}\n\nTo jest test mechanizmu odtwarzania sesji z obsługą tagów i harmonogramu.`,
      draft: true, // Zapisz jako draft, żeby nie spamować
      tags: ['test', 'automation', 'substack'], // Test tagów
      // scheduledTime: new Date(Date.now() + 60 * 60 * 1000).toISOString() // Test harmonogramu (za godzinę) - zakomentowane
    };
    
    const result = await adapter.publishPost(testPost);
    
    console.log('\n✅ Test zakończony pomyślnie!');
    console.log('Wynik:', result);
    
    // Poczekaj 5 sekund, żeby użytkownik mógł sprawdzić rezultat
    console.log('\nPoczekaj 5 sekund, żeby sprawdzić rezultat w przeglądarce...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    
  } catch (error) {
    console.error('\n❌ Test nie powiódł się:', error.message);
    process.exit(1);
  } finally {
    // Zamknij przeglądarkę
    await adapter.close();
  }
}

// Uruchom test
testSubstackAdapter();