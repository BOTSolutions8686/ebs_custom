const routes = [
	{
		path: "/salary-adjustment/new",
		name: "SalaryAdjustmentFormView",
		component: () => import("@/views/ebs_custom/GenericHRForm.vue"),
		props: { doctype: "Salary Adjustment Request" },
	},
	{
		path: "/salary-adjustment/:id",
		name: "SalaryAdjustmentDetailView",
		component: () => import("@/views/ebs_custom/GenericHRForm.vue"),
		props: (route) => ({
			doctype: "Salary Adjustment Request",
			id: route.params.id,
		}),
	},
	{
		path: "/promotion-request/new",
		name: "PromotionRequestFormView",
		component: () => import("@/views/ebs_custom/GenericHRForm.vue"),
		props: { doctype: "Promotion Request" },
	},
	{
		path: "/promotion-request/:id",
		name: "PromotionRequestDetailView",
		component: () => import("@/views/ebs_custom/GenericHRForm.vue"),
		props: (route) => ({
			doctype: "Promotion Request",
			id: route.params.id,
		}),
	},
	{
		path: "/branch-attendance-approval/new",
		name: "BranchAttendanceApprovalFormView",
		component: () => import("@/views/ebs_custom/BranchAttendanceApprovalForm.vue"),
	},
	{
		path: "/branch-attendance-approval/:id",
		name: "BranchAttendanceApprovalDetailView",
		component: () => import("@/views/ebs_custom/BranchAttendanceApprovalForm.vue"),
		props: (route) => ({
			id: route.params.id,
		}),
	},
]

export default routes
