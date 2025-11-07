/**
 * Script to verify and fix facility IDs for all permit monitors
 */

const { initializeDatabase, permitQueries, saveDatabase } = require('./db');
const https = require('https');

// Known correct facility IDs based on investigation
const KNOWN_FACILITIES = {
  'gates of lodore': '250014',  // Dinosaur Green And Yampa River Permits
  'yampa river': '250014',      // Same facility, different division
  'deerlodge park': '250014',   // Same facility, different division
  'san juan river': '234621',   // San Juan River
  'desolation canyon': '233393', // Desolation Gray - Green River Permit
  'grand canyon': '233262',     // Grand Canyon River
};

/**
 * Test if a facility ID is valid
 */
function testFacilityId(facilityId) {
  return new Promise((resolve) => {
    const url = `https://www.recreation.gov/api/permits/${facilityId}`;

    https.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    }, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const json = JSON.parse(data);
            if (json.payload) {
              resolve({
                valid: true,
                facilityName: json.payload.facility_name || 'Unknown',
                divisions: json.payload.divisions || {},
                data: json.payload
              });
            } else {
              resolve({ valid: false, error: 'No payload in response' });
            }
          } catch (e) {
            resolve({ valid: false, error: 'Invalid JSON' });
          }
        } else {
          resolve({ valid: false, error: `HTTP ${res.statusCode}` });
        }
      });
    }).on('error', (e) => {
      resolve({ valid: false, error: e.message });
    });
  });
}

/**
 * Search for facility by name
 */
function searchFacilityByName(name) {
  return new Promise((resolve) => {
    const searchUrl = `https://www.recreation.gov/api/search?q=${encodeURIComponent(name)}&entity_type=permit`;

    https.get(searchUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    }, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const json = JSON.parse(data);
            if (json.results && json.results.length > 0) {
              resolve(json.results[0].entity_id);
            } else {
              resolve(null);
            }
          } catch (e) {
            resolve(null);
          }
        } else {
          resolve(null);
        }
      });
    }).on('error', () => {
      resolve(null);
    });
  });
}

/**
 * Update a permit's facility ID
 */
function updatePermitFacilityId(permitId, userId, newFacilityId) {
  const db = require('./db').db();

  db.run(
    'UPDATE permits SET facility_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?',
    [newFacilityId, permitId, userId]
  );

  saveDatabase();
}

/**
 * Sleep helper
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log('='.repeat(70));
  console.log('Facility ID Verification and Fix Script');
  console.log('='.repeat(70));

  // Initialize database
  await initializeDatabase();

  // Get all enabled permits
  const permits = permitQueries.getAllEnabled.all();

  if (permits.length === 0) {
    console.log('\nNo permits found in database!');
    return;
  }

  console.log(`\nFound ${permits.length} permit(s) to check\n`);

  const updatesNeeded = [];

  for (const permit of permits) {
    console.log('\n' + '='.repeat(70));
    console.log(`Permit #${permit.id}: ${permit.name}`);
    console.log(`User: ${permit.email}`);
    console.log(`Current Facility ID: ${permit.facility_id}`);
    console.log('='.repeat(70));

    // FIRST: Check if this matches a known facility
    const nameLower = permit.name.toLowerCase();
    let knownCorrectId = null;

    for (const [knownName, knownId] of Object.entries(KNOWN_FACILITIES)) {
      if (nameLower.includes(knownName)) {
        knownCorrectId = knownId;
        console.log(`\nMatches known facility: "${knownName}" -> ${knownId}`);
        break;
      }
    }

    // If we have a known correct ID and current ID doesn't match
    if (knownCorrectId && permit.facility_id !== knownCorrectId) {
      console.log(`✗ WRONG FACILITY ID!`);
      console.log(`  Current: ${permit.facility_id}`);
      console.log(`  Should be: ${knownCorrectId}`);

      updatesNeeded.push({
        permitId: permit.id,
        userId: permit.user_id,
        permitName: permit.name,
        oldId: permit.facility_id,
        newId: knownCorrectId,
        reason: 'Matched known facility'
      });

      await sleep(500);
      continue;
    }

    // Test current facility ID
    console.log('Testing current facility ID...');
    const result = await testFacilityId(permit.facility_id);

    if (result.valid) {
      console.log('✓ Facility ID is VALID');
      console.log(`  Recreation.gov Name: ${result.facilityName}`);
      if (result.divisions) {
        const divEntries = Object.entries(result.divisions).slice(0, 5);
        if (divEntries.length > 0) {
          console.log(`  Divisions (${Object.keys(result.divisions).length}):`);
          for (const [divId, divInfo] of divEntries) {
            console.log(`    - ${divId}: ${divInfo.name || 'Unknown'}`);
          }
        } else {
          console.log(`  ⚠️  WARNING: No divisions found - may not have availability data`);
        }
      }
    } else {
      console.log('✗ Facility ID is INVALID');
      console.log(`  Error: ${result.error}`);

      // Try to find correct facility ID
      console.log('\n  Searching for correct facility ID...');

      let correctId = null;

      // Search recreation.gov
      console.log(`  Searching recreation.gov for: ${permit.name}`);
      correctId = await searchFacilityByName(permit.name);
      if (correctId) {
        console.log(`  Found via search: ${correctId}`);
        // Verify it's valid
        const verify = await testFacilityId(correctId);
        if (verify.valid) {
          console.log(`  Verified: ${verify.facilityName}`);
        } else {
          console.log('  Search result was invalid, ignoring');
          correctId = null;
        }
      }

      if (correctId && correctId !== permit.facility_id) {
        updatesNeeded.push({
          permitId: permit.id,
          userId: permit.user_id,
          permitName: permit.name,
          oldId: permit.facility_id,
          newId: correctId,
          reason: 'Found via search'
        });
      } else {
        console.log('  ✗ Could not find correct facility ID');
      }
    }

    await sleep(500); // Be nice to the API
  }

  // Show summary of updates needed
  console.log('\n' + '='.repeat(70));
  console.log('UPDATE SUMMARY');
  console.log('='.repeat(70));

  if (updatesNeeded.length === 0) {
    console.log('\n✓ All facility IDs are valid! No updates needed.');
    return;
  }

  console.log(`\nFound ${updatesNeeded.length} permit(s) that need updating:\n`);
  for (const update of updatesNeeded) {
    console.log(`  Permit #${update.permitId}: ${update.permitName}`);
    console.log(`    ${update.oldId} → ${update.newId}`);
    if (update.reason) {
      console.log(`    Reason: ${update.reason}`);
    }
    console.log();
  }

  // Apply updates automatically
  console.log('Applying updates...');
  for (const update of updatesNeeded) {
    process.stdout.write(`  Updating permit #${update.permitId}... `);
    try {
      updatePermitFacilityId(update.permitId, update.userId, update.newId);
      console.log('✓');
    } catch (error) {
      console.log(`✗ Error: ${error.message}`);
    }
  }

  console.log('\n✓ Updates complete!');
  console.log('\nRecommendation: Run the "Check Permits Now" feature to verify the fixes.');
}

main().catch(error => {
  console.error('Error:', error);
  process.exit(1);
});
