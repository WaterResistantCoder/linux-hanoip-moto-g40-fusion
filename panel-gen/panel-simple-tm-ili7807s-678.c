// SPDX-License-Identifier: GPL-2.0-only
// Copyright (c) 2013, The Linux Foundation. All rights reserved.

static const struct drm_display_mode tm_ili7807s_678_mode = {
	.clock = (1080 + 28 + 4 + 24) * (2460 + 2565 + 2 + 12) * 60 / 1000,
	.hdisplay = 1080,
	.hsync_start = 1080 + 28,
	.hsync_end = 1080 + 28 + 4,
	.htotal = 1080 + 28 + 4 + 24,
	.vdisplay = 2460,
	.vsync_start = 2460 + 2565,
	.vsync_end = 2460 + 2565 + 2,
	.vtotal = 2460 + 2565 + 2 + 12,
	.width_mm = 69,
	.height_mm = 158,
	.type = DRM_MODE_TYPE_DRIVER,
};

static const struct panel_desc_dsi tm_ili7807s_678 = {
	.desc = {
		.modes = &tm_ili7807s_678_mode,
		.num_modes = 1,
		.bpc = 8,
		.size = {
			.width = 69,
			.height = 158,
		},
		.connector_type = DRM_MODE_CONNECTOR_DSI,
	},
	.flags = MIPI_DSI_MODE_VIDEO | MIPI_DSI_CLOCK_NON_CONTINUOUS,
	.format = MIPI_DSI_FMT_RGB888,
	.lanes = 4,
};
