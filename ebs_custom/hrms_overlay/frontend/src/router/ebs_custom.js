const genericForm = () => import("@/views/ebs_custom/GenericHRForm.vue")
const attendanceForm = () => import("@/views/ebs_custom/BranchAttendanceApprovalForm.vue")

const forms = [
	["salary-adjustment", "Salary Adjustment Request", genericForm],
	["promotion-request", "Promotion Request", genericForm],
	["branch-attendance-approval", "Branch Attendance Approval", attendanceForm],
	["branch-transfer-request", "Branch Transfer Request", genericForm],
	["shift-transfer-request", "Shift Transfer Request", genericForm],
	["salary-statement-request", "Salary Statement Request", genericForm],
	["resignation-request", "Resignation Request", genericForm],
	["offboarding-interview", "Offboarding Interview", genericForm],
	["employee-complaint", "Employee Complaint", genericForm],
	["employee-data-adjustment", "Employee Data Adjustment Request", genericForm],
]

const routes = forms.flatMap(([path, doctype, component]) => {
	const name = doctype.replace(/\s+/g, "")
	return [
		{
			path: `/${path}/new`,
			name: `${name}FormView`,
			component,
			props: component === attendanceForm ? undefined : { doctype },
		},
		{
			path: `/${path}/:id`,
			name: `${name}DetailView`,
			component,
			props: (route) =>
				component === attendanceForm
					? { id: route.params.id }
					: { doctype, id: route.params.id },
		},
	]
})

export default routes
