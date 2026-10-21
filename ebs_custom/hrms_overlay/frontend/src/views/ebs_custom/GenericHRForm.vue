<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				:doctype="doctype"
				v-model="doc"
				:isSubmittable="true"
				:fields="formFields.data"
				:id="props.id"
			/>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { ref, inject, watch } from "vue"

import FormView from "@/components/FormView.vue"

const sessionEmployee = inject("$employee")

const props = defineProps({
	doctype: {
		type: String,
		required: true,
	},
	id: {
		type: String,
		required: false,
	},
})

const doc = ref({})

const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: props.doctype },
	transform(data) {
		const exclude = ["naming_series", "amended_from", "workflow_state"]
		if (!props.id) {
			exclude.push("employee_update_applied", "update_scheduled", "status", "initiated_by")
		}
		return data.filter((field) => !exclude.includes(field.fieldname))
	},
})
formFields.reload()

watch(
	() => sessionEmployee.data?.name,
	(employee) => {
		if (employee && !props.id && !doc.value.employee) {
			doc.value.employee = employee
		}
	},
	{ immediate: true },
)
</script>
