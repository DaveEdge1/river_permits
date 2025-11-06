/**
 * Permits routes
 */

const express = require('express');
const router = express.Router();
const { permitQueries, notificationQueries } = require('../db');
const { requireAuth } = require('../auth');
const RIVERS = require('../rivers');

// All routes require authentication
router.use(requireAuth);

/**
 * GET /api/permits
 * Get all permits for current user
 */
router.get('/', (req, res) => {
  try {
    const permits = permitQueries.findByUserId.all(req.session.userId);
    res.json({ permits });
  } catch (error) {
    console.error('Get permits error:', error);
    res.status(500).json({ error: 'Failed to fetch permits' });
  }
});

/**
 * GET /api/permits/rivers
 * Get list of available rivers
 */
router.get('/rivers', (req, res) => {
  res.json({ rivers: RIVERS });
});

/**
 * POST /api/permits
 * Create a new permit
 */
router.post('/', (req, res) => {
  try {
    const {
      name,
      facility_id,
      start_date,
      end_date,
      min_people = 1,
      max_people = 25,
      enabled = 1
    } = req.body;

    // Validation
    if (!name || !facility_id || !start_date || !end_date) {
      return res.status(400).json({
        error: 'Missing required fields: name, facility_id, start_date, end_date'
      });
    }

    // Validate dates
    const startDate = new Date(start_date);
    const endDate = new Date(end_date);

    if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
      return res.status(400).json({ error: 'Invalid date format' });
    }

    if (startDate > endDate) {
      return res.status(400).json({ error: 'Start date must be before end date' });
    }

    // Create permit
    const result = permitQueries.create.run(
      req.session.userId,
      name,
      facility_id,
      start_date,
      end_date,
      min_people,
      max_people,
      enabled ? 1 : 0
    );

    // Fetch the created permit
    const permit = permitQueries.findById.get(result.lastInsertRowid);

    res.json({ success: true, permit });
  } catch (error) {
    console.error('Create permit error:', error);
    res.status(500).json({ error: 'Failed to create permit' });
  }
});

/**
 * PUT /api/permits/:id
 * Update a permit
 */
router.put('/:id', (req, res) => {
  try {
    const permitId = parseInt(req.params.id);
    const {
      name,
      facility_id,
      start_date,
      end_date,
      min_people,
      max_people,
      enabled
    } = req.body;

    // Validation
    if (!name || !facility_id || !start_date || !end_date) {
      return res.status(400).json({
        error: 'Missing required fields'
      });
    }

    // Validate dates
    const startDate = new Date(start_date);
    const endDate = new Date(end_date);

    if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
      return res.status(400).json({ error: 'Invalid date format' });
    }

    if (startDate > endDate) {
      return res.status(400).json({ error: 'Start date must be before end date' });
    }

    // Update permit
    const result = permitQueries.update.run(
      name,
      facility_id,
      start_date,
      end_date,
      min_people || 1,
      max_people || 25,
      enabled ? 1 : 0,
      permitId,
      req.session.userId
    );

    if (result.changes === 0) {
      return res.status(404).json({ error: 'Permit not found or unauthorized' });
    }

    // Fetch updated permit
    const permit = permitQueries.findById.get(permitId);

    res.json({ success: true, permit });
  } catch (error) {
    console.error('Update permit error:', error);
    res.status(500).json({ error: 'Failed to update permit' });
  }
});

/**
 * DELETE /api/permits/:id
 * Delete a permit
 */
router.delete('/:id', (req, res) => {
  try {
    const permitId = parseInt(req.params.id);

    const result = permitQueries.delete.run(permitId, req.session.userId);

    if (result.changes === 0) {
      return res.status(404).json({ error: 'Permit not found or unauthorized' });
    }

    res.json({ success: true });
  } catch (error) {
    console.error('Delete permit error:', error);
    res.status(500).json({ error: 'Failed to delete permit' });
  }
});

/**
 * PATCH /api/permits/:id/toggle
 * Toggle permit enabled status
 */
router.patch('/:id/toggle', (req, res) => {
  try {
    const permitId = parseInt(req.params.id);
    const { enabled } = req.body;

    const result = permitQueries.toggleEnabled.run(
      enabled ? 1 : 0,
      permitId,
      req.session.userId
    );

    if (result.changes === 0) {
      return res.status(404).json({ error: 'Permit not found or unauthorized' });
    }

    const permit = permitQueries.findById.get(permitId);

    res.json({ success: true, permit });
  } catch (error) {
    console.error('Toggle permit error:', error);
    res.status(500).json({ error: 'Failed to toggle permit' });
  }
});

/**
 * GET /api/permits/notifications
 * Get recent notifications for current user
 */
router.get('/notifications', (req, res) => {
  try {
    const notifications = notificationQueries.getRecentByUser.all(req.session.userId);
    res.json({ notifications });
  } catch (error) {
    console.error('Get notifications error:', error);
    res.status(500).json({ error: 'Failed to fetch notifications' });
  }
});

module.exports = router;
