/**
 * Mobile permits routes (JWT-authenticated)
 * Same functionality as permits.js but uses JWT auth for mobile apps
 */

const express = require('express');
const router = express.Router();
const { permitQueries, notificationQueries } = require('../db');
const { requireJwtAuth } = require('../jwt-auth');
const rivers = require('../rivers');

// Helper function to fetch availability from recreation.gov
async function fetchAvailability(facilityId, startDate, endDate) {
  const results = [];

  try {
    // Fetch facility info to get division names
    const facilityUrl = `https://www.recreation.gov/api/permits/${facilityId}`;
    const facilityResponse = await fetch(facilityUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    let divisionNames = {};
    if (facilityResponse.ok) {
      const facilityData = await facilityResponse.json();
      if (facilityData.payload && facilityData.payload.divisions) {
        for (const [divId, divInfo] of Object.entries(facilityData.payload.divisions)) {
          divisionNames[divId] = divInfo.name || 'Unknown Section';
        }
      }
    }

    // Parse dates
    const start = new Date(startDate);
    const end = new Date(endDate);

    // Check each month in the date range
    let current = new Date(start.getFullYear(), start.getMonth(), 1);
    const endMonth = new Date(end.getFullYear(), end.getMonth(), 1);

    while (current <= endMonth) {
      const monthStr = current.toISOString();
      const availUrl = `https://www.recreation.gov/api/permits/${facilityId}/availability/month?start_date=${monthStr}`;

      const availResponse = await fetch(availUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
      });

      if (availResponse.ok) {
        const availData = await availResponse.json();

        if (availData.payload && availData.payload.availability) {
          for (const [divisionId, divisionInfo] of Object.entries(availData.payload.availability)) {
            if (!divisionInfo || !divisionInfo.date_availability) continue;

            for (const [dateStr, permitInfo] of Object.entries(divisionInfo.date_availability)) {
              const permitDate = new Date(dateStr);

              // Check if date is in our range
              if (permitDate >= start && permitDate <= end) {
                const remaining = permitInfo.remaining || 0;

                if (remaining > 0) {
                  results.push({
                    date: dateStr.substring(0, 10),
                    division_id: divisionId,
                    division_name: divisionNames[divisionId] || 'Unknown Section',
                    remaining: remaining
                  });
                }
              }
            }
          }
        }
      }

      // Move to next month
      current.setMonth(current.getMonth() + 1);
    }
  } catch (error) {
    console.error(`Error fetching availability for ${facilityId}:`, error);
  }

  return results;
}

/**
 * GET /api/mobile/permits
 * Get all permits for the authenticated user
 */
router.get('/', requireJwtAuth, (req, res) => {
  try {
    const permits = permitQueries.findByUserId.all(req.userId);

    // Add river name to each permit
    const permitsWithRiverNames = permits.map(permit => {
      const river = rivers.find(r => r.id === permit.facility_id);
      return {
        ...permit,
        riverName: river ? river.name : 'Unknown River',
        // Normalize snake_case to camelCase
        userId: permit.user_id,
        facilityId: permit.facility_id,
        startDate: permit.start_date,
        endDate: permit.end_date,
        partySize: permit.party_size,
        createdAt: permit.created_at,
        updatedAt: permit.updated_at
      };
    });

    res.json({ permits: permitsWithRiverNames });
  } catch (error) {
    console.error('Get permits error:', error);
    res.status(500).json({ error: 'Failed to get permits' });
  }
});

/**
 * POST /api/mobile/permits
 * Create a new permit
 */
router.post('/', requireJwtAuth, (req, res) => {
  try {
    const {
      name,
      facilityId,
      startDate,
      endDate,
      partySize,
      enabled
    } = req.body;

    // Validate required fields
    if (!name || !facilityId || !startDate || !endDate) {
      return res.status(400).json({
        error: 'Missing required fields: name, facilityId, startDate, endDate'
      });
    }

    // Validate facility ID exists (rivers use 'id' property)
    const river = rivers.find(r => r.id === facilityId);
    if (!river) {
      return res.status(400).json({ error: 'Invalid facility ID' });
    }

    // Validate dates
    const start = new Date(startDate);
    const end = new Date(endDate);
    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
      return res.status(400).json({ error: 'Invalid date format' });
    }
    if (start > end) {
      return res.status(400).json({ error: 'Start date must be before end date' });
    }

    // Validate party size
    const size = partySize || 1;
    if (size < 1 || size > 50) {
      return res.status(400).json({ error: 'Invalid party size' });
    }

    // Create the permit
    const result = permitQueries.create.run(
      req.userId,
      name,
      facilityId,
      startDate,
      endDate,
      size,
      enabled !== false ? 1 : 0
    );

    res.status(201).json({
      success: true,
      permitId: result.lastInsertRowid,
      message: 'Permit created successfully'
    });
  } catch (error) {
    console.error('Create permit error:', error);
    res.status(500).json({ error: 'Failed to create permit' });
  }
});

/**
 * PUT /api/mobile/permits/:id
 * Update a permit
 */
router.put('/:id', requireJwtAuth, (req, res) => {
  try {
    const permitId = parseInt(req.params.id);
    const {
      name,
      facilityId,
      startDate,
      endDate,
      partySize,
      enabled
    } = req.body;

    // Check permit exists and belongs to user
    const existing = permitQueries.findById.get(permitId);
    if (!existing || existing.user_id !== req.userId) {
      return res.status(404).json({ error: 'Permit not found' });
    }

    // Use existing values for any fields not provided
    const updatedName = name || existing.name;
    const updatedFacilityId = facilityId || existing.facility_id;
    const updatedStartDate = startDate || existing.start_date;
    const updatedEndDate = endDate || existing.end_date;
    const updatedPartySize = partySize !== undefined ? partySize : existing.party_size;
    const updatedEnabled = enabled !== undefined ? (enabled ? 1 : 0) : existing.enabled;

    // Update the permit
    permitQueries.update.run(
      updatedName,
      updatedFacilityId,
      updatedStartDate,
      updatedEndDate,
      updatedPartySize,
      updatedEnabled,
      permitId,
      req.userId
    );

    res.json({
      success: true,
      message: 'Permit updated successfully'
    });
  } catch (error) {
    console.error('Update permit error:', error);
    res.status(500).json({ error: 'Failed to update permit' });
  }
});

/**
 * DELETE /api/mobile/permits/:id
 * Delete a permit and its notification history
 */
router.delete('/:id', requireJwtAuth, (req, res) => {
  try {
    const permitId = parseInt(req.params.id);

    // First verify the permit exists and belongs to this user
    const existing = permitQueries.findById.get(permitId);
    if (!existing || existing.user_id !== req.userId) {
      return res.status(404).json({ error: 'Permit not found' });
    }

    // Delete notifications for this permit (safe now that we've verified ownership)
    notificationQueries.deleteByPermitId.run(permitId);

    // Then delete the permit
    permitQueries.delete.run(permitId, req.userId);

    res.json({
      success: true,
      message: 'Permit deleted successfully'
    });
  } catch (error) {
    console.error('Delete permit error:', error);
    res.status(500).json({ error: 'Failed to delete permit' });
  }
});

/**
 * PATCH /api/mobile/permits/:id/toggle
 * Toggle permit enabled/disabled
 */
router.patch('/:id/toggle', requireJwtAuth, (req, res) => {
  try {
    const permitId = parseInt(req.params.id);

    // Get current permit
    const permit = permitQueries.findById.get(permitId);

    if (!permit || permit.user_id !== req.userId) {
      return res.status(404).json({ error: 'Permit not found' });
    }

    // Toggle enabled status
    const newEnabled = permit.enabled === 1 ? 0 : 1;
    permitQueries.toggleEnabled.run(newEnabled, permitId, req.userId);

    res.json({
      success: true,
      enabled: newEnabled === 1,
      message: `Permit ${newEnabled === 1 ? 'enabled' : 'disabled'}`
    });
  } catch (error) {
    console.error('Toggle permit error:', error);
    res.status(500).json({ error: 'Failed to toggle permit' });
  }
});

/**
 * GET /api/mobile/permits/rivers
 * Get list of available rivers
 */
router.get('/rivers', requireJwtAuth, (req, res) => {
  // Map river data to match expected DTO format (id -> facilityId)
  const mappedRivers = rivers.map(r => ({
    name: r.name,
    facilityId: r.id,
    description: r.description || r.location
  }));
  res.json({ rivers: mappedRivers });
});

/**
 * GET /api/mobile/permits/notifications
 * Get recent notifications for the user
 */
router.get('/notifications', requireJwtAuth, (req, res) => {
  try {
    const notifications = notificationQueries.getRecentByUser.all(req.userId);

    // Add river names and normalize field names
    const notificationsWithDetails = notifications.map(n => {
      // Find the permit to get river info
      const permit = permitQueries.findById.get(n.permit_id);
      const river = permit ? rivers.find(r => r.facilityId === permit.facility_id) : null;

      return {
        id: n.id,
        permitId: n.permit_id,
        date: n.date,
        divisionId: n.division_id,
        divisionName: n.division_name,
        remaining: n.remaining,
        notifiedAt: n.notified_at,
        riverName: river ? river.name : (permit ? permit.name : 'Unknown'),
        permitName: permit ? permit.name : 'Unknown'
      };
    });

    res.json({ notifications: notificationsWithDetails });
  } catch (error) {
    console.error('Get notifications error:', error);
    res.status(500).json({ error: 'Failed to get notifications' });
  }
});

/**
 * GET /api/mobile/permits/availability
 * Get current availability for user's permits
 * Optional query param: facilityId - filter to a specific facility
 */
router.get('/availability', requireJwtAuth, async (req, res) => {
  try {
    const { facilityId } = req.query;

    // Get user's permits
    const permits = permitQueries.findByUserId.all(req.userId);

    // Filter permits - if facilityId provided, get that permit; otherwise get all enabled
    let targetPermits;
    if (facilityId) {
      targetPermits = permits.filter(p => p.facility_id === facilityId);
    } else {
      targetPermits = permits.filter(p => p.enabled === 1);
    }

    if (targetPermits.length === 0) {
      return res.json({ rivers: [], totalCount: 0, riverCount: 0 });
    }

    const riverResults = [];
    let totalCount = 0;

    // Check availability for each permit
    for (const permit of targetPermits) {
      const river = rivers.find(r => r.id === permit.facility_id);
      const riverName = river ? river.name : permit.name;

      const availability = await fetchAvailability(
        permit.facility_id,
        permit.start_date,
        permit.end_date
      );

      if (availability.length > 0) {
        totalCount += availability.length;
        riverResults.push({
          permit_name: riverName,
          facility_id: permit.facility_id,
          permit_count: availability.length,
          permits: availability,
          has_more: false
        });
      }
    }

    res.json({
      rivers: riverResults,
      totalCount: totalCount,
      riverCount: riverResults.length
    });
  } catch (error) {
    console.error('Get availability error:', error);
    res.status(500).json({ error: 'Failed to get availability' });
  }
});

module.exports = router;
