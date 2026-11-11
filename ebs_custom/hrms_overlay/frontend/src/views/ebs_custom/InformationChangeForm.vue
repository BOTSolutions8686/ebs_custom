<template>
	<ion-page>
		<ion-content class="ion-padding">
			<div class="flex flex-col w-full sm:w-96 gap-4 p-4">
				<header class="flex flex-row items-center">
					<Button variant="ghost" class="!pl-0" @click="router.back()">
						<FeatherIcon name="chevron-left" class="h-5 w-5" />
					</Button>
					<h2 class="text-xl font-semibold text-gray-900">{{ __("Change My Information") }}</h2>
				</header>

				<label class="text-sm text-gray-700">{{ __("Field") }}</label>
				<select v-model="fieldLabel" class="border rounded px-3 py-2">
					<option value="">{{ __("Select") }}</option>
					<option v-for="field in fields.data || []" :key="field.fieldname" :value="field.label">
						{{ __(field.label) }}
					</option>
				</select>

				<div v-if="selected" class="text-sm text-gray-600">
					{{ __("Current Value") }}: {{ selected.current_value || __("Empty") }}
				</div>

				<label class="text-sm text-gray-700">{{ __("New Value") }}</label>
				<input v-model="newValue" class="border rounded px-3 py-2" type="text" />

				<label class="text-sm text-gray-700">{{ __("Reason") }}</label>
				<textarea v-model="reason" class="border rounded px-3 py-2" rows="3"></textarea>

				<Button variant="solid" :loading="submitRequest.loading" @click="save">
					{{ __("Submit") }}
				</Button>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { Button, FeatherIcon, createResource, toast } from "frappe-ui"
import { computed, inject, ref } from "vue"
import { useRouter } from "vue-router"

const __ = inject("$translate")
const router = useRouter()
const fieldLabel = ref("")
const newValue = ref("")
const reason = ref("")

const fields = createResource({
	url: "ebs_custom.hr_requests.api.get_information_fields",
	auto: true,
})

const selected = computed(() => (fields.data || []).find((field) => field.label === fieldLabel.value))

const submitRequest = createResource({
	url: "ebs_custom.hr_requests.api.submit_information_change",
	onSuccess(data) {
		toast({ title: __("Request submitted"), text: data.name })
		router.back()
	},
	onError(error) {
		toast({ title: __("Error"), text: error.messages?.[0] || __("Could not submit the request") })
	},
})

const save = () => {
	submitRequest.submit({
		field_label: fieldLabel.value,
		new_value: newValue.value,
		reason: reason.value,
	})
}
</script>
