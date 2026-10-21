import os
import re
import shutil
import subprocess

import frappe

# Only copy these paths from hrms_overlay (safe — won't break core hrms)
OVERLAY_COPY_PATHS = [
	"frontend/src/views/ebs_custom",
	"frontend/src/views/ChangePassword.vue",
	"frontend/src/views/AppSettings.vue",
	"frontend/src/views/Profile.vue",
	"frontend/src/router/ebs_custom.js",
	"frontend/src/components/icons/FrappeHRLogo.vue",
	"frontend/src/components/RequestPanel.vue",
	"frontend/src/components/RequestList.vue",
	"frontend/src/components/EmployeeAdvanceItem.vue",
	"frontend/src/data/advances.js",
	"frontend/src/data/config/requestSummaryFields.js",
	"hrms/public/manifest",
]


def execute():
	apply_hrms_pwa_overlay()


def apply_hrms_pwa_overlay():
	"""Copy HRMS PWA customizations from ebs_custom into the hrms app."""
	if "hrms" not in frappe.get_installed_apps():
		frappe.logger().info("ebs_custom: hrms not installed, skipping PWA overlay")
		return False

	overlay_root = os.path.join(frappe.get_app_path("ebs_custom"), "hrms_overlay")
	if not os.path.isdir(overlay_root):
		frappe.logger().warning("ebs_custom: hrms_overlay folder missing")
		return False

	hrms_root = frappe.get_app_path("hrms", "..")

	_copy_overlay_files(overlay_root, hrms_root)
	_patch_router_index(hrms_root)
	_patch_home_vue(hrms_root)
	_patch_hooks(hrms_root)
	_patch_branding_files(hrms_root)
	_patch_vite_manifest(hrms_root)

	frappe.logger().info("ebs_custom: HRMS PWA overlay applied from ebs_custom/hrms_overlay")
	return True


def build_hrms_pwa():
	"""Try to build HRMS frontend after overlay. Returns True on success."""
	hrms_root = frappe.get_app_path("hrms", "..")
	frontend_dir = os.path.join(hrms_root, "frontend")
	bench_path = frappe.utils.get_bench_path()

	if not os.path.isdir(frontend_dir):
		return False

	yarn = shutil.which("yarn")
	if not yarn:
		frappe.logger().warning("ebs_custom: yarn not found — skip auto PWA build")
		return False

	install_cmds = [
		[yarn, "install", "--frozen-lockfile"],
		[yarn, "install"],
	]

	for install_cmd in install_cmds:
		try:
			result = subprocess.run(
				install_cmd,
				cwd=frontend_dir,
				capture_output=True,
				text=True,
				timeout=600,
			)
			if result.returncode == 0:
				break
			frappe.logger().warning(
				f"ebs_custom: yarn install failed ({' '.join(install_cmd)}): {result.stderr[-2000:]}"
			)
		except (subprocess.TimeoutExpired, OSError) as exc:
			frappe.logger().warning(f"ebs_custom: yarn install error: {exc}")
			return False
	else:
		return False

	try:
		result = subprocess.run(
			[yarn, "build"],
			cwd=frontend_dir,
			capture_output=True,
			text=True,
			timeout=900,
		)
		if result.returncode != 0:
			frappe.log_error(
				title="ebs_custom PWA build failed",
				message=result.stderr or result.stdout or "Unknown yarn build error",
			)
			return False

		bench_cmd = os.path.join(bench_path, "env", "bin", "bench")
		if not os.path.isfile(bench_cmd):
			bench_cmd = shutil.which("bench") or "bench"

		subprocess.run(
			[bench_cmd, "build", "--app", "hrms"],
			cwd=bench_path,
			check=True,
			capture_output=True,
			text=True,
			timeout=600,
		)
		return True
	except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
		frappe.log_error(title="ebs_custom PWA build failed", message=str(exc))
		return False


def _copy_overlay_files(overlay_root, hrms_root):
	for rel_path in OVERLAY_COPY_PATHS:
		src = os.path.join(overlay_root, rel_path.replace("/", os.sep))
		if not os.path.exists(src):
			continue

		dst = os.path.join(hrms_root, rel_path.replace("/", os.sep))
		if os.path.isdir(src):
			if os.path.isdir(dst):
				shutil.rmtree(dst)
			shutil.copytree(src, dst)
		else:
			os.makedirs(os.path.dirname(dst), exist_ok=True)
			shutil.copy2(src, dst)


def _patch_router_index(hrms_root):
	path = os.path.join(hrms_root, "frontend", "src", "router", "index.js")
	if not os.path.isfile(path):
		return

	with open(path, encoding="utf-8") as handle:
		content = handle.read()

	import_line = 'import ebsCustomRoutes from "./ebs_custom"'
	spread_line = "\t...ebsCustomRoutes,"

	# Remove duplicate imports / spreads from earlier buggy patch runs
	while content.count(import_line) > 1:
		content = content.replace(import_line + "\n", "", 1)

	content = re.sub(r"(\t\.\.\.ebsCustomRoutes,\n)+", spread_line + "\n", content)

	if import_line not in content:
		if 'import salarySlipRoutes from "./salary_slips"\n' in content:
			content = content.replace(
				'import salarySlipRoutes from "./salary_slips"\n',
				'import salarySlipRoutes from "./salary_slips"\n' + import_line + "\n",
			)
		elif 'import salarySlipRoutes from "./salary_slips"' in content:
			content = content.replace(
				'import salarySlipRoutes from "./salary_slips"',
				'import salarySlipRoutes from "./salary_slips"\n' + import_line,
			)

	if spread_line not in content:
		for pattern, replacement in [
			("\t...salarySlipRoutes,\n]", "\t...salarySlipRoutes,\n" + spread_line + "\n]"),
			("...salarySlipRoutes,\n]", "...salarySlipRoutes,\n\t...ebsCustomRoutes,\n]"),
		]:
			if pattern.split("\n")[0] in content:
				content = content.replace(pattern, replacement)
				break

	# Change Password route (newer HRMS PWA feature — keep via overlay on older hrms)
	if 'name: "ChangePassword"' not in content:
		change_password_route = """\t{
\t\tpath: "/change-password",
\t\tname: "ChangePassword",
\t\tcomponent: () => import("@/views/ChangePassword.vue"),
\t},
"""
		if 'name: "Settings"' in content and 'path: "/settings"' in content:
			content = content.replace(
				'\t{\n\t\tpath: "/settings",\n\t\tname: "Settings",\n\t\tcomponent: () => import("@/views/AppSettings.vue"),\n\t},',
				'\t{\n\t\tpath: "/settings",\n\t\tname: "Settings",\n\t\tcomponent: () => import("@/views/AppSettings.vue"),\n\t},\n'
				+ change_password_route,
			)
		elif 'path: "/invalid-employee"' in content:
			content = content.replace(
				'\t{\n\t\tpath: "/invalid-employee",',
				change_password_route + '\t{\n\t\tpath: "/invalid-employee",',
			)

	with open(path, "w", encoding="utf-8") as handle:
		handle.write(content)


def _patch_home_vue(hrms_root):
	path = os.path.join(hrms_root, "frontend", "src", "views", "Home.vue")
	if not os.path.isfile(path):
		return

	with open(path, encoding="utf-8") as handle:
		content = handle.read()

	if "SalaryAdjustmentFormView" in content:
		return

	quick_links = """
	{
		icon: markRaw(SalaryIcon),
		title: __("Salary Adjustment"),
		route: "SalaryAdjustmentFormView",
	},
	{
		icon: markRaw(LeaveIcon),
		title: __("Promotion Request"),
		route: "PromotionRequestFormView",
	},
	{
		icon: markRaw(AttendanceIcon),
		title: __("Branch Attendance Approval"),
		route: "BranchAttendanceApprovalFormView",
	},
]"""

	for pattern in [
		'\t\troute: "SalarySlipsDashboard",\n\t},\n]',
		'\t\troute: "SalarySlipsDashboard",\n\t},\r\n]',
	]:
		if pattern in content:
			content = content.replace(pattern, '\t\troute: "SalarySlipsDashboard",\n\t},' + quick_links)
			break

	with open(path, "w", encoding="utf-8") as handle:
		handle.write(content)


def _patch_hooks(hrms_root):
	path = os.path.join(hrms_root, "hooks.py")
	if not os.path.isfile(path):
		return

	with open(path, encoding="utf-8") as handle:
		content = handle.read()

	content = re.sub(r'app_title\s*=\s*"[^"]*"', 'app_title = "BOT HR"', content)
	content = re.sub(r'("title":\s*)"Frappe HR"', r'\1"BOT HR"', content)

	with open(path, "w", encoding="utf-8") as handle:
		handle.write(content)


def _patch_branding_files(hrms_root):
	replacements = {
		os.path.join(hrms_root, "frontend", "src", "views", "Login.vue"): [
			("Login to Frappe HR", "Login to BOT HR"),
		],
		os.path.join(hrms_root, "frontend", "src", "components", "BaseLayout.vue"): [
			('__("Frappe HR")', '__("BOT HR")'),
		],
		os.path.join(hrms_root, "frontend", "src", "components", "InstallPrompt.vue"): [
			("Install Frappe HR", "Install BOT HR"),
		],
	}

	for path, pairs in replacements.items():
		if not os.path.isfile(path):
			continue
		with open(path, encoding="utf-8") as handle:
			content = handle.read()
		for old, new in pairs:
			content = content.replace(old, new)
		with open(path, "w", encoding="utf-8") as handle:
			handle.write(content)


def _bot_hr_icons_available(hrms_root):
	manifest_dir = os.path.join(hrms_root, "hrms", "public", "manifest")
	required = ["bot-hr-icon-192.png", "bot-hr-icon-512.png"]
	return all(os.path.isfile(os.path.join(manifest_dir, name)) for name in required)


def _patch_vite_manifest(hrms_root):
	path = os.path.join(hrms_root, "frontend", "vite.config.js")
	if not os.path.isfile(path):
		return

	with open(path, encoding="utf-8") as handle:
		content = handle.read()

	content = re.sub(r'name:\s*"[^"]*"', 'name: "BOT HR"', content, count=1)
	content = re.sub(r'short_name:\s*"[^"]*"', 'short_name: "BOT HR"', content, count=1)

	if 'description: "BOT HR' not in content and "description:" in content:
		content = re.sub(
			r'description:\s*"[^"]*"',
			'description: "BOT HR — Elite Business Company HR & Payroll"',
			content,
			count=1,
		)

	if "scope:" not in content and "start_url:" in content:
		content = content.replace('start_url: "/hrms",', 'start_url: "/hrms",\n\t\t\t\tscope: "/hrms",')

	frappe_icon_192 = "/assets/hrms/manifest/manifest-icon-192.maskable.png"
	frappe_icon_512 = "/assets/hrms/manifest/manifest-icon-512.maskable.png"
	bot_icon_192 = "/assets/hrms/manifest/bot-hr-icon-192.png"
	bot_icon_512 = "/assets/hrms/manifest/bot-hr-icon-512.png"

	if _bot_hr_icons_available(hrms_root):
		content = content.replace(frappe_icon_192, bot_icon_192)
		content = content.replace(frappe_icon_512, bot_icon_512)
	else:
		# Keep default HRMS icons so Chrome still shows Install / Download app
		content = content.replace(bot_icon_192, frappe_icon_192)
		content = content.replace(bot_icon_512, frappe_icon_512)
		frappe.logger().warning(
			"ebs_custom: BOT HR icons missing — using default HRMS PWA icons for install prompt"
		)

	with open(path, "w", encoding="utf-8") as handle:
		handle.write(content)
