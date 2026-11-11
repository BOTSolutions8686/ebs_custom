<template>
	<ion-page>
		<ion-content class="ion-padding">
			<div class="flex flex-col w-full sm:w-96">
				<header class="flex flex-row items-center bg-white border-b py-4 px-3">
					<Button variant="ghost" class="!pl-0" @click="router.back()">
						<FeatherIcon name="chevron-left" class="h-5 w-5" />
					</Button>
					<h2 class="text-xl font-semibold text-gray-900">{{ __("Pending Requests") }}</h2>
				</header>

				<div v-if="requests.loading" class="p-4 text-gray-600">{{ __("Loading") }}</div>
				<div v-else-if="!requests.data?.length" class="p-4 text-gray-600">
					{{ __("You have no pending requests") }}
				</div>
				<button
					v-for="item in requests.data"
					:key="item.doctype + item.name"
					class="flex flex-col items-start border-b bg-white p-4 text-left w-full"
					@click="openRequest(item)"
				>
					<div class="text-base font-medium text-gray-900">{{ __(item.doctype) }}</div>
					<div class="text-sm text-gray-700">{{ item.title }} · {{ item.name }}</div>
					<div class="text-sm text-gray-500">{{ item.status }}<span v-if="item.date"> · {{ item.date }}</span></div>
				</button>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { Button, FeatherIcon, createResource } from "frappe-ui"
import { inject } from "vue"
import { useRouter } from "vue-router"

const __ = inject("$translate")
const router = useRouter()

const requests = createResource({
	url: "ebs_custom.hr_requests.api.get_pending_requests",
	auto: true,
})

const openRequest = (item) => {
	if (!item.route) return
	router.push({ name: item.route, params: { id: item.name } })
}
</script>
