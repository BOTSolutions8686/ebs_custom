<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<div v-if="formFields.data" class="flex flex-col h-full">
				<div
					v-if="!props.id && !doc.excel_generated"
					class="px-4 pt-3 pb-2 bg-white border-b"
				>
					<Button
						variant="solid"
						class="w-full"
						:loading="loadCheckins.loading"
						@click="handleLoadCheckins"
					>
						{{ __("Load Check-ins") }}
					</Button>
					<p class="text-xs text-gray-500 mt-2 text-center">
						{{ __("Select Branch and Attendance Date first, then load employees.") }}
					</p>
				</div>
				<FormView
					:doctype="doctype"
					v-model="doc"
					:isSubmittable="true"
					:fields="formFields.data"
					:id="props.id"
				/>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { Button, createResource, toast } from "frappe-ui"
import { ref, inject } from "vue"

import FormView from "@/components/FormView.vue"

const __ = inject("$translate")

const doctype = "Branch Attendance Approval"

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

const doc = ref({ employees: [] })

const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype },
	transform(data) {
		const exclude = ["naming_series", "amended_from", "workflow_state", "excel_generated", "report_file"]
		return data.filter((field) => !exclude.includes(field.fieldname))
	},
})
formFields.reload()

const managerDefaults = createResource({
	url: "ebs_custom.attendance.events.attendance.get_branch_manager_defaults",
	auto: !props.id,
	onSuccess(data) {
		if (!data || props.id) return
		if (!doc.value.branch && data.custom_branch) {
			doc.value.branch = data.custom_branch
		}
		if (!doc.value.company && data.company) {
			doc.value.company = data.company
		}
	},
})

const loadCheckins = createResource({
	url: "ebs_custom.attendance.events.attendance.load_branch_checkins",
	makeParams() {
		return {
			branch: doc.value.branch,
			attendance_date: doc.value.attendance_date,
		}
	},
	auto: false,
	onSuccess(rows) {
		if (!rows?.length) {
			toast({
				title: __("No employees"),
				text: __("No employees found for this branch."),
				icon: "alert-circle",
				position: "bottom-center",
				iconClasses: "text-red-500",
			})
			return
		}

		doc.value.employees = rows.map((row) => ({
			employee: row.employee,
			employee_name: row.employee_name,
			employee_id: row.employee_id,
			check_in_time: row.check_in_time,
			check_out_time: row.check_out_time,
			status: row.status,
			doctype: "Branch Attendance Approval Detail",
		}))

		toast({
			title: __("Loaded"),
			text: __("{0} employee(s) loaded", [rows.length]),
			icon: "check-circle",
			position: "bottom-center",
			iconClasses: "text-green-500",
		})
	},
})

function handleLoadCheckins() {
	if (!doc.value.branch || !doc.value.attendance_date) {
		toast({
			title: __("Required"),
			text: __("Please select Branch and Attendance Date first."),
			icon: "alert-circle",
			position: "bottom-center",
			iconClasses: "text-red-500",
		})
		return
	}
	loadCheckins.reload()
}
</script>
