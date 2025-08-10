#!/usr/bin/env node

require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });
const { SubstackAdapter } = require('../src/adapters/substack-adapter');

async function testSessionManagement() {
  console.log('🧪 Test Session Management - Walidacja i rotacja sesji');
  console.log('=====================================================\n');
  
  const adapter = new SubstackAdapter();
  
  try {
    // Test 1: Inicjalizacja z sprawdzaniem statusu
    console.log('1️⃣ Test inicjalizacji z automatycznym sprawdzaniem statusu...');
    await adapter.initialize('personal');
    
    // Test 2: Sprawdzenie statusu sesji
    console.log('\n2️⃣ Test sprawdzania statusu sesji...');
    const status = await adapter.checkSessionStatus();
    
    console.log('📊 Status sesji:');
    console.log(`   Konto: ${status.account}`);
    console.log(`   Status: ${status.status}`);
    console.log(`   Wygasła: ${status.expired ? 'TAK' : 'NIE'}`);
    console.log(`   Dni do wygaśnięcia: ${status.daysLeft}`);
    console.log(`   Data wygaśnięcia: ${status.validUntil.toLocaleDateString()}`);
    console.log(`   Data utworzenia: ${status.createdAt.toLocaleDateString()}`);
    
    // Test 3: Sprawdzenie czy wymaga odnowienia
    console.log('\n3️⃣ Test sprawdzania potrzeby odnowienia...');
    const needsRenewal7 = await adapter.needsRenewal(7);
    const needsRenewal14 = await adapter.needsRenewal(14);
    
    console.log(`🔄 Wymaga odnowienia (7 dni): ${needsRenewal7 ? 'TAK' : 'NIE'}`);
    console.log(`⏰ Wymaga odnowienia (14 dni): ${needsRenewal14 ? 'TAK' : 'NIE'}`);
    
    // Test 4: Rekomendacje
    console.log('\n4️⃣ Rekomendacje:');
    if (status.expired) {
      console.log('❌ Sesja wygasła - wymagane natychmiastowe odnowienie');
      console.log('💡 Uruchom: node scripts/substack-cli.js session renew --account personal');
    } else if (status.status === 'critical') {
      console.log('🚨 Sesja krytyczna - odnów w ciągu 1-2 dni');
      console.log('💡 Uruchom: node scripts/substack-cli.js session renew --account personal');
    } else if (status.status === 'warning') {
      console.log('⚠️ Sesja wygasa wkrótce - zaplanuj odnowienie');
      console.log('💡 Uruchom: node scripts/substack-cli.js session renew --account personal');
    } else {
      console.log('✅ Sesja w dobrej kondycji');
      console.log('📅 Następne sprawdzenie za ~' + Math.max(1, status.daysLeft - 7) + ' dni');
    }
    
    console.log('\n✅ Test session management zakończony pomyślnie!');
    
  } catch (error) {
    console.error('\n❌ Test nie powiódł się:', error.message);
    
    if (error.message.includes('Nie znaleziono pliku sesji')) {
      console.log('\n💡 Utwórz sesję przed testem:');
      console.log('node scripts/substack-cli.js session create --account personal');
    } else if (error.message.includes('wygasła')) {
      console.log('\n💡 Odnów wygasłą sesję:');
      console.log('node scripts/substack-cli.js session renew --account personal');
    }
    
    process.exit(1);
  }
}

// Uruchom test
testSessionManagement();