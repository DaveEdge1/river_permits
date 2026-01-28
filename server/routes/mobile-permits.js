/**
 * Mobile permits routes (JWT-authenticated)
 * Same functionality as permits.js but uses JWT auth for mobile apps
 */

const express = require('express');
const router = express.Router();
const { permitQueries, notificationQueries } = require('../db');
const { requireJwtAuth } = require('../jwt-auth');
const rivers = require('../rivers');

/**
 * GET /api/mobile/permits
 * Get all permits for the authenticated user
 */
router.get('/', requireJwtAuth, (req, res) => {
  try {
    const permits = permitQueries.findByUserId.all(req.userId);

    // Add river name to each permit
    const permitsWithRiverNames = permits.map(permit => {
      const river = rivers.find(r => r.facilityId === permit.facility_id);
      return {
        ...permit,
        riverName: river ? river.name : 'Unknown River',
        // Normalize snake_case to camelCase
        userId: permit.user_id,
        facilityId: permit.facility_id,
        startDate: permit.start_date,
        endDate: permit.end_date,
        minPeople: permit.min_people,
        maxPeople: permit.max_people,
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
      minPeople,
      maxPeople,
      enabled
    } = req.body;

    // Validate required fields
    if (!name || !facilityId || !startDate || !endDate) {
      return res.status(400).json({
        error: 'Missing required fields: name, facilityId, startDate, endDate'
      });
    }

    // Validate facility ID exists
    const river = rivers.find(r => r.facilityId === facilityId);
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
    const min = minPeople || 1;
    const max = maxPeople || 25;
    if (min < 1 || max > 50 || min > max) {
      return res.status(400).json({ error: 'Invalid party size range' });
    }

    // Create the permit
    const result = permitQueries.create.run(
      req.userId,
      name,
      facilityId,
      startDate,
      endDate,
      min,
      max,
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
      minPeople,
      maxPeople,
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
    const updatedMinPeople = minPeople !== undefined ? minPeople : existing.min_people;
    const updatedMaxPeople = maxPeople !== undefined ? maxPeople : existing.max_people;
    const updatedEnabled = enabled !== undefined ? (enabled ? 1 : 0) : existing.enabled;

    // Update the permit
    permitQueries.update.run(
      updatedName,
      updatedFacilityId,
      updatedStartDate,
      updatedEndDate,
      updatedMinPeople,
      updatedMaxPeople,
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
 * Delete a permit
 */
router.delete('/:id', requireJwtAuth, (req, res) => {
  try {
    const permitId = parseInt(req.params.id);

    const result = permitQueries.delete.run(permitId, req.userId);

    if (result.changes === 0) {
      return res.status(404).json({ error: 'Permit not found' });
    }

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
  res.json({ rivers });
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

module.exports = router;
