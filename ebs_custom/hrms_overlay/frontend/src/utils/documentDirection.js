import dayjs from "@/utils/dayjs"
import "dayjs/locale/ar"
import "dayjs/locale/tr"

const RTL_TARGETS = "ion-app, ion-page, ion-content, ion-header, ion-toolbar, ion-tab-bar, ion-modal"

export function applyDocumentDirection() {
	const lang = (window.frappe?.boot?.lang || "en").split("-")[0]
	const rtl = lang === "ar"
	const dir = rtl ? "rtl" : "ltr"

	document.documentElement.lang = lang
	document.documentElement.dir = dir
	if (document.body) document.body.dir = dir
	dayjs.locale(lang === "ar" || lang === "tr" ? lang : "en")

	const mark = () => {
		document.querySelectorAll(RTL_TARGETS).forEach((el) => {
			if (el.getAttribute("dir") !== dir) el.setAttribute("dir", dir)
		})
	}

	mark()
	if (!window.__ebsDirObserver && document.body) {
		window.__ebsDirObserver = new MutationObserver(mark)
		window.__ebsDirObserver.observe(document.body, { childList: true, subtree: true })
	}
}
