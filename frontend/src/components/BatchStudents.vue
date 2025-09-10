<template>
	<div v-if="batch.data" class="">
		<div class="w-full flex items-center justify-between pb-4">
			<div class="font-medium text-ink-gray-7">
				{{ __('Statistics') }}
			</div>
		</div>
		<div class="grid grid-cols-2 md:grid-cols-4 gap-5 mb-8">
			<NumberChart
				class="border rounded-md"
				:config="{ title: __('Students'), value: students.data?.length || 0 }"
			/>

			<NumberChart
				class="border rounded-md"
				:config="{
					title: __('Certified'),
					value: certificationCount.data || 0,
				}"
			/>

			<NumberChart
				class="border rounded-md"
				:config="{
					title: __('Courses'),
					value: batch.data.courses?.length || 0,
				}"
			/>

			<NumberChart
				class="border rounded-md"
				:config="{ title: __('Assessments'), value: assessmentCount || 0 }"
			/>
		</div>

		<AxisChart
			v-if="showProgressChart"
			:config="{
				data: chartData,
				title: __('Batch Summary'),
				subtitle: __('Progress of students in courses and assessments'),
				xAxis: {
					key: 'task',
					title: 'Tasks',
					type: 'category',
				},
				yAxis: {
					title: __('Number of Students'),
					echartOptions: {
						minInterval: 1,
					},
				},
				swapXY: true,
				series: [
					{
						name: 'value',
						type: 'bar',
					},
				],
			}"
		/>
	</div>

	<div>
                <div class="flex items-center justify-between mb-4">
                        <div class="text-ink-gray-7 font-medium">
                                {{ __('Students') }}
                        </div>
                        <div class="flex gap-2">
                                <Button v-if="students.data?.length" @click="exportToCSV">
                                        {{ __('Export Excel') }}
                                </Button>
                                <Button v-if="students.data?.length" @click="exportToPDF">
                                        {{ __('Export PDF') }}
                                </Button>
                                <Button v-if="!readOnlyMode" @click="openStudentModal()">
                                        <template #prefix>
                                                <Plus class="h-4 w-4" />
                                        </template>
                                        {{ __('Add') }}
                                </Button>
                        </div>
                </div>

		<div v-if="students.data?.length">
			<ListView
				:columns="getStudentColumns()"
				:rows="students.data"
				row-key="name"
				:options="{
					showTooltip: false,
				}"
			>
				<ListHeader
					class="mb-2 grid items-center space-x-4 rounded bg-surface-gray-2 p-2"
				>
					<ListHeaderItem
						:item="item"
						v-for="item in getStudentColumns()"
						:title="item.label"
					>
						<template #prefix="{ item }">
							<FeatherIcon
								v-if="item.icon"
								:name="item.icon"
								class="h-4 w-4 stroke-1.5"
							/>
						</template>
					</ListHeaderItem>
				</ListHeader>
				<ListRows>
					<ListRow
						:row="row"
						v-for="row in students.data"
						class="group cursor-pointer"
						@click="openStudentProgressModal(row)"
					>
						<template #default="{ column, item }">
							<ListRowItem
								:item="row[column.key]"
								:align="column.align"
								class="text-sm"
							>
								<template #prefix>
									<div v-if="column.key == 'full_name'">
										<Avatar
											class="flex items-center"
											:image="row['user_image']"
											:label="item"
											size="sm"
										/>
									</div>
								</template>
                                                                <div
                                                                        :class="{
                                                                                'text-green-600':
                                                                                        (column.key === 'assignments_todo' &&
                                                                                                row.assignments_complete) ||
                                                                                        (column.key === 'quizzes_todo' &&
                                                                                                row.quizzes_complete),
                                                                        }"
                                                                >
                                                                        {{ row[column.key] }}
                                                                </div>
                                                        </ListRowItem>
                                                </template>
                                        </ListRow>
                                </ListRows>
				<ListSelectBanner>
					<template #actions="{ unselectAll, selections }">
						<div class="flex gap-2">
							<Button
								variant="ghost"
								@click="removeStudents(selections, unselectAll)"
							>
								<Trash2 class="h-4 w-4 stroke-1.5" />
							</Button>
						</div>
					</template>
				</ListSelectBanner>
			</ListView>
		</div>
		<div v-else class="text-sm italic text-ink-gray-5">
			{{ __('There are no students in this batch.') }}
		</div>
	</div>

	<StudentModal
		:batch="props.batch.data.name"
		v-model="showStudentModal"
		v-model:reloadStudents="students"
		v-model:batchModal="props.batch"
	/>
	<BatchStudentProgress
		:student="selectedStudent"
		v-model="showStudentProgressModal"
	/>
</template>
<script setup>
import {
	Avatar,
	AxisChart,
	Button,
	createResource,
	FeatherIcon,
	ListHeader,
	ListHeaderItem,
	ListSelectBanner,
	ListRow,
	ListRows,
	ListView,
	ListRowItem,
	NumberChart,
	toast,
} from 'frappe-ui'
import {
        Plus,
        Trash2,
} from 'lucide-vue-next'
import { ref, watch } from 'vue'
import StudentModal from '@/components/Modals/StudentModal.vue'
import BatchStudentProgress from '@/components/Modals/BatchStudentProgress.vue'

const showStudentModal = ref(false)
const showStudentProgressModal = ref(false)
const selectedStudent = ref(null)
const chartData = ref(null)
const showProgressChart = ref(false)
const assessmentCount = ref(0)
const readOnlyMode = window.read_only_mode

const props = defineProps({
	batch: {
		type: Object,
		default: null,
	},
})

const students = createResource({
	url: 'lms.lms.utils.get_batch_students',
	params: {
		batch: props.batch?.data?.name,
	},
	auto: true,
        onSuccess(data) {
                data.forEach((row) => {
                        const assignments = []
                        const quizzes = []
                        Object.keys(row.assessments).forEach((title) => {
                                const info = row.assessments[title]
                                const type = (info.type || '').toLowerCase()
                                if (!info.submission) {
                                        if (type.includes('assignment')) {
                                                assignments.push(title)
                                        } else if (type.includes('quiz')) {
                                                quizzes.push(title)
                                        }
                                }
                        })
                        const hasAssignments = Object.values(row.assessments).some((i) =>
                                (i.type || '').toLowerCase().includes('assignment')
                        )
                        const hasQuizzes = Object.values(row.assessments).some((i) =>
                                (i.type || '').toLowerCase().includes('quiz')
                        )
                        if (hasAssignments && assignments.length === 0) {
                                row.assignments_todo = 'ส่งครบแล้ว'
                                row.assignments_complete = true
                        } else {
                                row.assignments_todo = assignments.join(', ')
                                row.assignments_complete = false
                        }
                        if (hasQuizzes && quizzes.length === 0) {
                                row.quizzes_todo = 'ส่งครบแล้ว'
                                row.quizzes_complete = true
                        } else {
                                row.quizzes_todo = quizzes.join(', ')
                                row.quizzes_complete = false
                        }
                })
                chartData.value = getChartData()
                showProgressChart.value =
                        data.length &&
                        (props.batch?.data?.courses?.length || assessmentCount.value)
        },
})

const getStudentColumns = () => {
        let columns = [
                {
                        label: 'Full Name',
                        key: 'full_name',
                        width: '20rem',
                        icon: 'user',
                },
                {
                        label: 'Assignment To Do',
                        key: 'assignments_todo',
                        width: '15rem',
                        icon: 'book',
                },
                {
                        label: 'Quiz To Do',
                        key: 'quizzes_todo',
                        width: '15rem',
                        icon: 'help-circle',
                },
                {
                        label: 'Last Active',
                        key: 'last_active',
                        width: '10rem',
                        align: 'center',
                        icon: 'clock',
                },
        ]

	return columns
}

const openStudentModal = () => {
	showStudentModal.value = true
}

const openStudentProgressModal = (row) => {
        showStudentProgressModal.value = true
        selectedStudent.value = row
}

const exportToCSV = () => {
        if (!students.data?.length) return
        const rows = [
                ['Full Name', 'Assignments To Do', 'Quizzes To Do', 'Last Active'],
        ]
        students.data.forEach((row) => {
                rows.push([
                        row.full_name,
                        row.assignments_todo || '',
                        row.quizzes_todo || '',
                        row.last_active || '',
                ])
        })
        const csvContent = rows
                .map((e) => e.map((v) => `"${v}"`).join(','))
                .join('\n')
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.setAttribute('download', 'students.csv')
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
}

const exportToPDF = () => {
        if (!students.data?.length) return
        let html =
                '<html><head><title>Students</title></head><body><table border="1" style="border-collapse:collapse;width:100%"><tr><th>Full Name</th><th>Assignments To Do</th><th>Quizzes To Do</th><th>Last Active</th></tr>'
        students.data.forEach((row) => {
                html += `<tr><td>${row.full_name}</td><td>${row.assignments_todo || ''}</td><td>${row.quizzes_todo || ''}</td><td>${row.last_active || ''}</td></tr>`
        })
        html += '</table></body></html>'
        const w = window.open('')
        w.document.write(html)
        w.document.close()
        w.focus()
        w.print()
}

const deleteStudents = createResource({
	url: 'lms.lms.api.delete_documents',
	makeParams(values) {
		return {
			doctype: 'LMS Batch Enrollment',
			documents: values.students,
		}
	},
})

const removeStudents = (selections, unselectAll) => {
	deleteStudents.submit(
		{
			students: Array.from(selections),
		},
		{
			onSuccess(data) {
				students.reload()
				props.batch.reload()
				toast.success(__('Students deleted successfully'))
				unselectAll()
			},
		}
	)
}

const getChartData = () => {
	let tasks = []
	let data = []

	students.data.forEach((row) => {
		tasks = countAssessments(row, tasks)
		tasks = countCourses(row, tasks)
	})

	tasks.forEach((task) => {
		data.push({
			task: task.label,
			value: task.value,
		})
	})
	return data
}

const countAssessments = (row, tasks) => {
        Object.keys(row.assessments).forEach((assessment) => {
                if (row.assessments[assessment].submission) {
                        tasks.filter((task) => task.label === assessment).length
                                ? tasks.filter((task) => task.label === assessment)[0].value++
                                : tasks.push({
                                                value: 1,
                                                label: assessment,
                                  })
                }
        })
	return tasks
}

const countCourses = (row, tasks) => {
	Object.keys(row.courses).forEach((course) => {
		if (row.courses[course] === 100) {
			tasks.filter((task) => task.label === course).length
				? tasks.filter((task) => task.label === course)[0].value++
				: tasks.push({
						value: 1,
						label: course,
				  })
		}
	})
	return tasks
}

watch(students, () => {
	if (students.data?.length) {
		assessmentCount.value = Object.keys(students.data?.[0].assessments).length
	}
})

const certificationCount = createResource({
	url: 'frappe.client.get_count',
	params: {
		doctype: 'LMS Certificate',
		filters: {
			batch_name: props.batch?.data?.name,
		},
	},
	auto: true,
})
</script>
