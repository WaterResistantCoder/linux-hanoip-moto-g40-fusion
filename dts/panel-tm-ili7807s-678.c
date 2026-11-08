// SPDX-License-Identifier: GPL-2.0-only
// Copyright (c) 2026 FIXME
// Generated with linux-mdss-dsi-panel-driver-generator from vendor device tree:
//   Copyright (c) 2013, The Linux Foundation. All rights reserved. (FIXME)

#include <linux/delay.h>
#include <linux/device-id/of.h>
#include <linux/gpio/consumer.h>
#include <linux/module.h>

#include <video/mipi_display.h>

#include <drm/display/drm_dsc.h>
#include <drm/display/drm_dsc_helper.h>
#include <drm/drm_mipi_dsi.h>
#include <drm/drm_modes.h>
#include <drm/drm_panel.h>
#include <drm/drm_probe_helper.h>

struct tm_ili7807s_678 {
	struct drm_panel panel;
	struct mipi_dsi_device *dsi;
	struct drm_dsc_config dsc;
	struct gpio_desc *reset_gpio;
};

static inline
struct tm_ili7807s_678 *to_tm_ili7807s_678(struct drm_panel *panel)
{
	return container_of_const(panel, struct tm_ili7807s_678, panel);
}

static void tm_ili7807s_678_reset(struct tm_ili7807s_678 *ctx)
{
	gpiod_set_value_cansleep(ctx->reset_gpio, 0);
	usleep_range(4000, 5000);
	gpiod_set_value_cansleep(ctx->reset_gpio, 1);
	usleep_range(1000, 2000);
	gpiod_set_value_cansleep(ctx->reset_gpio, 0);
	usleep_range(12000, 13000);
}

static int tm_ili7807s_678_on(struct tm_ili7807s_678 *ctx)
{
	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

	ctx->dsi->mode_flags |= MIPI_DSI_MODE_LPM;

	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x78, 0x07, 0x00);
	mipi_dsi_dcs_exit_sleep_mode_multi(&dsi_ctx);
	mipi_dsi_msleep(&dsi_ctx, 120);
	mipi_dsi_dcs_set_display_on_multi(&dsi_ctx);
	mipi_dsi_msleep(&dsi_ctx, 20);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x78, 0x07, 0x06);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, MIPI_DCS_READ_MEMORY_CONTINUE,
				     0xe3);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x80, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x78, 0x07, 0x08);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfd, 0x00, 0x9f);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xe1, 0xd9);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfd, 0x00, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x78, 0x07, 0x00);
	mipi_dsi_dcs_set_display_brightness_multi(&dsi_ctx, 0x3203);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, MIPI_DCS_WRITE_CONTROL_DISPLAY,
				     0x2c);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, MIPI_DCS_WRITE_POWER_SAVE, 0x01);

	return dsi_ctx.accum_err;
}

static int tm_ili7807s_678_off(struct tm_ili7807s_678 *ctx)
{
	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

	ctx->dsi->mode_flags &= ~MIPI_DSI_MODE_LPM;

	mipi_dsi_dcs_set_display_off_multi(&dsi_ctx);
	mipi_dsi_msleep(&dsi_ctx, 50);
	mipi_dsi_dcs_enter_sleep_mode_multi(&dsi_ctx);
	mipi_dsi_msleep(&dsi_ctx, 150);

	return dsi_ctx.accum_err;
}

static int tm_ili7807s_678_prepare(struct drm_panel *panel)
{
	struct tm_ili7807s_678 *ctx = to_tm_ili7807s_678(panel);
	struct device *dev = &ctx->dsi->dev;
	struct drm_dsc_picture_parameter_set pps;
	int ret;

	tm_ili7807s_678_reset(ctx);

	ret = tm_ili7807s_678_on(ctx);
	if (ret < 0) {
		dev_err(dev, "Failed to initialize panel: %d\n", ret);
		gpiod_set_value_cansleep(ctx->reset_gpio, 1);
		return ret;
	}

	drm_dsc_pps_payload_pack(&pps, &ctx->dsc);

	ret = mipi_dsi_picture_parameter_set(ctx->dsi, &pps);
	if (ret < 0) {
		dev_err(panel->dev, "failed to transmit PPS: %d\n", ret);
		return ret;
	}

	ret = mipi_dsi_compression_mode(ctx->dsi, true);
	if (ret < 0) {
		dev_err(dev, "failed to enable compression mode: %d\n", ret);
		return ret;
	}

	msleep(28); /* TODO: Is this panel-dependent? */

	return 0;
}

static int tm_ili7807s_678_unprepare(struct drm_panel *panel)
{
	struct tm_ili7807s_678 *ctx = to_tm_ili7807s_678(panel);
	struct device *dev = &ctx->dsi->dev;
	int ret;

	ret = tm_ili7807s_678_off(ctx);
	if (ret < 0)
		dev_err(dev, "Failed to un-initialize panel: %d\n", ret);

	gpiod_set_value_cansleep(ctx->reset_gpio, 1);

	return 0;
}

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

static int tm_ili7807s_678_get_modes(struct drm_panel *panel,
				     struct drm_connector *connector)
{
	return drm_connector_helper_get_modes_fixed(connector, &tm_ili7807s_678_mode);
}

static const struct drm_panel_funcs tm_ili7807s_678_panel_funcs = {
	.prepare = tm_ili7807s_678_prepare,
	.unprepare = tm_ili7807s_678_unprepare,
	.get_modes = tm_ili7807s_678_get_modes,
};

static int tm_ili7807s_678_probe(struct mipi_dsi_device *dsi)
{
	struct device *dev = &dsi->dev;
	struct tm_ili7807s_678 *ctx;
	int ret;

	ctx = devm_drm_panel_alloc(dev, struct tm_ili7807s_678, panel,
				   &tm_ili7807s_678_panel_funcs,
				   DRM_MODE_CONNECTOR_DSI);
	if (IS_ERR(ctx))
		return PTR_ERR(ctx);

	ctx->reset_gpio = devm_gpiod_get(dev, "reset", GPIOD_OUT_HIGH);
	if (IS_ERR(ctx->reset_gpio))
		return dev_err_probe(dev, PTR_ERR(ctx->reset_gpio),
				     "Failed to get reset-gpios\n");

	ctx->dsi = dsi;
	mipi_dsi_set_drvdata(dsi, ctx);

	dsi->lanes = 4;
	dsi->format = MIPI_DSI_FMT_RGB888;
	dsi->mode_flags = MIPI_DSI_MODE_VIDEO | MIPI_DSI_CLOCK_NON_CONTINUOUS;

	ctx->panel.prepare_prev_first = true;

	ret = drm_panel_of_backlight(&ctx->panel);
	if (ret)
		return dev_err_probe(dev, ret, "Failed to get backlight\n");

	ret = devm_drm_panel_add(dev, &ctx->panel);
	if (ret)
		return ret;

	/* This panel only supports DSC; unconditionally enable it */
	dsi->dsc = &ctx->dsc;

	ctx->dsc.dsc_version_major = 1;
	ctx->dsc.dsc_version_minor = 1;

	/* TODO: Pass slice_per_pkt = 2 */
	ctx->dsc.slice_height = 10;
	ctx->dsc.slice_width = 540;
	/*
	 * TODO: hdisplay should be read from the selected mode once
	 * it is passed back to drm_panel (in prepare?)
	 */
	WARN_ON(1080 % ctx->dsc.slice_width);
	ctx->dsc.slice_count = 1080 / ctx->dsc.slice_width;
	ctx->dsc.bits_per_component = 8;
	ctx->dsc.bits_per_pixel = 8 << 4; /* 4 fractional bits */
	ctx->dsc.block_pred_enable = true;

	return devm_mipi_dsi_attach(dev, dsi);
}

static const struct of_device_id tm_ili7807s_678_of_match[] = {
	{ .compatible = "tm,ili7807s-678" }, // FIXME
	{ /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, tm_ili7807s_678_of_match);

static struct mipi_dsi_driver tm_ili7807s_678_driver = {
	.probe = tm_ili7807s_678_probe,
	.driver = {
		.name = "panel-tm-ili7807s-678",
		.of_match_table = tm_ili7807s_678_of_match,
	},
};
module_mipi_dsi_driver(tm_ili7807s_678_driver);

MODULE_AUTHOR("linux-mdss-dsi-panel-driver-generator <fix@me>"); // FIXME
MODULE_DESCRIPTION("DRM driver for mipi_mot_vid_tm_ili7807s_fhd_678");
MODULE_LICENSE("GPL");
