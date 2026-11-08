// SPDX-License-Identifier: GPL-2.0-only
// Copyright (c) 2026 FIXME
// Generated with linux-mdss-dsi-panel-driver-generator from vendor device tree:
//   Copyright (c) 2014, The Linux Foundation. All rights reserved. (FIXME)

#ifndef _PANEL_TM_ILI7807S_678_FHD_VIDEO_H_
#define _PANEL_TM_ILI7807S_678_FHD_VIDEO_H_

#include <mipi_dsi.h>
#include <panel_display.h>
#include <panel.h>
#include <string.h>

static struct panel_config tm_ili7807s_678_fhd_video_panel_data = {
	.panel_node_id = "qcom,mdss_dsi_tm_ili7807s_678_fhd_video",
	.panel_controller = "dsi:0:",
	.panel_compatible = "qcom,mdss-dsi-panel",
	.panel_type = 0,
	.panel_destination = "DISPLAY_1",
	/* .panel_orientation not supported yet */
	.panel_framerate = 60,
	.panel_lp11_init = 1,
	.panel_init_delay = 0,
};

static struct panel_resolution tm_ili7807s_678_fhd_video_panel_res = {
	.panel_width = 1080,
	.panel_height = 2460,
	.hfront_porch = 28,
	.hback_porch = 24,
	.hpulse_width = 4,
	.hsync_skew = 0,
	.vfront_porch = 2565,
	.vback_porch = 12,
	.vpulse_width = 2,
	/* Borders not supported yet */
};

static struct color_info tm_ili7807s_678_fhd_video_color = {
	.color_format = 24,
	.color_order = DSI_RGB_SWAP_RGB,
	.underflow_color = 0xff,
	/* Borders and pixel packing not supported yet */
};

static char tm_ili7807s_678_fhd_video_on_cmd_0[] = {
	0x04, 0x00, 0x39, 0xc0, 0xff, 0x78, 0x07, 0x00
};
static char tm_ili7807s_678_fhd_video_on_cmd_1[] = {
	0x11, 0x00, 0x05, 0x80
};
static char tm_ili7807s_678_fhd_video_on_cmd_2[] = {
	0x29, 0x00, 0x05, 0x80
};
static char tm_ili7807s_678_fhd_video_on_cmd_3[] = {
	0x04, 0x00, 0x39, 0xc0, 0xff, 0x78, 0x07, 0x06
};
static char tm_ili7807s_678_fhd_video_on_cmd_4[] = {
	0x3e, 0xe3, 0x15, 0x80
};
static char tm_ili7807s_678_fhd_video_on_cmd_5[] = {
	0x80, 0x00, 0x15, 0x80
};
static char tm_ili7807s_678_fhd_video_on_cmd_6[] = {
	0x04, 0x00, 0x39, 0xc0, 0xff, 0x78, 0x07, 0x08
};
static char tm_ili7807s_678_fhd_video_on_cmd_7[] = {
	0x03, 0x00, 0x39, 0xc0, 0xfd, 0x00, 0x9f, 0xff
};
static char tm_ili7807s_678_fhd_video_on_cmd_8[] = {
	0xe1, 0xd9, 0x15, 0x80
};
static char tm_ili7807s_678_fhd_video_on_cmd_9[] = {
	0x03, 0x00, 0x39, 0xc0, 0xfd, 0x00, 0x00, 0xff
};
static char tm_ili7807s_678_fhd_video_on_cmd_10[] = {
	0x04, 0x00, 0x39, 0xc0, 0xff, 0x78, 0x07, 0x00
};
static char tm_ili7807s_678_fhd_video_on_cmd_11[] = {
	0x03, 0x00, 0x39, 0xc0, 0x51, 0x03, 0x32, 0xff
};
static char tm_ili7807s_678_fhd_video_on_cmd_12[] = {
	0x53, 0x2c, 0x15, 0x80
};
static char tm_ili7807s_678_fhd_video_on_cmd_13[] = {
	0x55, 0x01, 0x15, 0x80
};

static struct mipi_dsi_cmd tm_ili7807s_678_fhd_video_on_command[] = {
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_0), tm_ili7807s_678_fhd_video_on_cmd_0, 0 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_1), tm_ili7807s_678_fhd_video_on_cmd_1, 120 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_2), tm_ili7807s_678_fhd_video_on_cmd_2, 20 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_3), tm_ili7807s_678_fhd_video_on_cmd_3, 0 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_4), tm_ili7807s_678_fhd_video_on_cmd_4, 0 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_5), tm_ili7807s_678_fhd_video_on_cmd_5, 0 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_6), tm_ili7807s_678_fhd_video_on_cmd_6, 0 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_7), tm_ili7807s_678_fhd_video_on_cmd_7, 0 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_8), tm_ili7807s_678_fhd_video_on_cmd_8, 0 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_9), tm_ili7807s_678_fhd_video_on_cmd_9, 0 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_10), tm_ili7807s_678_fhd_video_on_cmd_10, 0 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_11), tm_ili7807s_678_fhd_video_on_cmd_11, 0 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_12), tm_ili7807s_678_fhd_video_on_cmd_12, 0 },
	{ sizeof(tm_ili7807s_678_fhd_video_on_cmd_13), tm_ili7807s_678_fhd_video_on_cmd_13, 0 },
};

static char tm_ili7807s_678_fhd_video_off_cmd_0[] = {
	0x28, 0x00, 0x05, 0x80
};
static char tm_ili7807s_678_fhd_video_off_cmd_1[] = {
	0x10, 0x00, 0x05, 0x80
};

static struct mipi_dsi_cmd tm_ili7807s_678_fhd_video_off_command[] = {
	{ sizeof(tm_ili7807s_678_fhd_video_off_cmd_0), tm_ili7807s_678_fhd_video_off_cmd_0, 50 },
	{ sizeof(tm_ili7807s_678_fhd_video_off_cmd_1), tm_ili7807s_678_fhd_video_off_cmd_1, 150 },
};

static struct command_state tm_ili7807s_678_fhd_video_state = {
	.oncommand_state = 0,
	.offcommand_state = 1,
};

static struct commandpanel_info tm_ili7807s_678_fhd_video_command_panel = {
	/* Unused, this is a video mode panel */
};

static struct videopanel_info tm_ili7807s_678_fhd_video_video_panel = {
	.hsync_pulse = 0,
	.hfp_power_mode = 0,
	.hbp_power_mode = 0,
	.hsa_power_mode = 0,
	.bllp_eof_power_mode = 1,
	.bllp_power_mode = 1,
	.traffic_mode = 1,
	/* This is bllp_eof_power_mode and bllp_power_mode combined */
	.bllp_eof_power = 1 << 3 | 1 << 0,
};

static struct lane_configuration tm_ili7807s_678_fhd_video_lane_config = {
	.dsi_lanes = 4,
	.dsi_lanemap = 0,
	.lane0_state = 1,
	.lane1_state = 1,
	.lane2_state = 1,
	.lane3_state = 1,
	.force_clk_lane_hs = 0,
};

static const uint32_t tm_ili7807s_678_fhd_video_timings[] = {
	
};

static struct panel_timing tm_ili7807s_678_fhd_video_timing_info = {
	.tclk_post = 0x0c,
	.tclk_pre = 0x30,
};

static struct panel_reset_sequence tm_ili7807s_678_fhd_video_reset_seq = {
	.pin_state = { 1, 0, 1 },
	.sleep = { 4, 1, 12 },
	.pin_direction = 2,
};

static struct backlight tm_ili7807s_678_fhd_video_backlight = {
	.bl_interface_type = BL_WLED,
	.bl_min_level = 1,
	.bl_max_level = 4095,
};

static inline void panel_tm_ili7807s_678_fhd_video_select(struct panel_struct *panel,
							  struct msm_panel_info *pinfo,
							  struct mdss_dsi_phy_ctrl *phy_db)
{
	panel->paneldata = &tm_ili7807s_678_fhd_video_panel_data;
	panel->panelres = &tm_ili7807s_678_fhd_video_panel_res;
	panel->color = &tm_ili7807s_678_fhd_video_color;
	panel->videopanel = &tm_ili7807s_678_fhd_video_video_panel;
	panel->commandpanel = &tm_ili7807s_678_fhd_video_command_panel;
	panel->state = &tm_ili7807s_678_fhd_video_state;
	panel->laneconfig = &tm_ili7807s_678_fhd_video_lane_config;
	panel->paneltiminginfo = &tm_ili7807s_678_fhd_video_timing_info;
	panel->panelresetseq = &tm_ili7807s_678_fhd_video_reset_seq;
	panel->backlightinfo = &tm_ili7807s_678_fhd_video_backlight;
	pinfo->mipi.panel_on_cmds = tm_ili7807s_678_fhd_video_on_command;
	pinfo->mipi.panel_off_cmds = tm_ili7807s_678_fhd_video_off_command;
	pinfo->mipi.num_of_panel_on_cmds = ARRAY_SIZE(tm_ili7807s_678_fhd_video_on_command);
	pinfo->mipi.num_of_panel_off_cmds = ARRAY_SIZE(tm_ili7807s_678_fhd_video_off_command);
	memcpy(phy_db->timing, tm_ili7807s_678_fhd_video_timings, TIMING_SIZE);
	phy_db->regulator_mode = DSI_PHY_REGULATOR_DCDC_MODE;
}

#endif /* _PANEL_TM_ILI7807S_678_FHD_VIDEO_H_ */
