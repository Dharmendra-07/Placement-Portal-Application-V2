<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Application & Placement History</h5>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else>
      <!-- Summary strip -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-2" v-for="s in summaryCards" :key="s.label">
          <div class="card border-0 shadow-sm text-center h-100">
            <div class="card-body py-3">
              <div class="fs-3 fw-bold" :class="s.color">{{ s.value }}</div>
              <div class="text-muted small mt-1">{{ s.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Filter + search -->
      <div class="d-flex gap-2 mb-3 flex-wrap align-items-center">
        <input v-model="search" type="text" class="form-control form-control-sm"
               style="max-width:260px"
               placeholder="Search company or job title..." />
        <div class="d-flex gap-1 flex-wrap">
          <button v-for="tab in tabs" :key="tab.value"
                  class="btn btn-sm"
                  :class="activeTab === tab.value
                    ? 'btn-primary' : 'btn-outline-secondary'"
                  @click="activeTab = tab.value">
            {{ tab.label }}
          </button>
        </div>
        <div class="ms-auto d-flex gap-2">
          <ExportButton role="student" />
          <button class="btn btn-sm btn-outline-secondary"
                  @click="exportCSV">
            Export (inline)
          </button>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="filtered.length === 0"
           class="text-muted text-center py-5">
        No records found.
      </div>

      <!-- Timeline cards -->
      <div v-else>
        <div v-for="a in filtered" :key="a.id"
             class="card border-0 shadow-sm mb-3">
          <div class="card-body py-3">
            <div class="row align-items-start g-2">

              <!-- Status indicator column -->
              <div class="col-auto d-flex flex-column align-items-center">
                <div class="rounded-circle d-flex align-items-center
                            justify-content-center fw-bold text-white"
                     :style="`width:38px;height:38px;font-size:12px;
                              background:${statusColor(a.status)}`">
                  {{ statusInitial(a.status) }}
                </div>
              </div>

              <!-- Main info -->
              <div class="col">
                <div class="d-flex justify-content-between align-items-start
                            flex-wrap gap-1">
                  <div>
                    <span class="fw-bold">{{ a.job_title }}</span>
                    <span class="text-muted small ms-2">— {{ a.company_name }}</span>
                  </div>
                  <span class="badge" :class="appBadge(a.status)">
                    {{ statusLabel(a.status) }}
                  </span>
                </div>

                <div class="text-muted small mt-1">
                  Applied: {{ formatDate(a.applied_at) }}
                  <span v-if="a.drive">
                    · {{ a.drive.job_type }}
                    · {{ a.drive.location || 'Remote' }}
                    <span v-if="a.drive.salary_min">
                      · ₹{{ a.drive.salary_min }}–{{ a.drive.salary_max }} LPA
                    </span>
                  </span>
                </div>

                <!-- Interview scheduled -->
                <div v-if="a.interview_date"
                     class="d-inline-flex align-items-center gap-2
                            mt-2 px-2 py-1 rounded"
                     style="background:var(--color-background-info)">
                  <span class="badge bg-info text-dark small">
                    {{ a.interview_type }}
                  </span>
                  <span class="small" style="color:var(--color-text-info)">
                    {{ formatDateTime(a.interview_date) }}
                  </span>
                  <span v-if="a.remarks" class="small text-muted">
                    · {{ a.remarks }}
                  </span>
                </div>

                <!-- Feedback / remarks -->
                <div v-else-if="a.remarks"
                     class="mt-2 small text-muted border-start border-3 ps-2"
                     :style="`border-color:${statusColor(a.status)} !important`">
                  {{ a.remarks }}
                </div>

                <!-- Placement confirmation -->
                <div v-if="a.placement"
                     class="alert alert-success py-2 px-3 small mb-0 mt-2">
                  <span class="fw-medium">Placed!</span>
                  Position: {{ a.placement.position }}
                  · ₹{{ a.placement.salary }} LPA
                  · Joining: {{ a.placement.joining_date || 'TBD' }}
                  <a v-if="a.placement.offer_letter_url"
                     :href="a.placement.offer_letter_url"
                     target="_blank"
                     class="btn btn-sm btn-success ms-2 py-0">
                    Offer Letter
                  </a>
                </div>

                <!-- Status history timeline (collapsible) -->
                <div v-if="parsedHistory(a).length > 0" class="mt-2">
                  <button class="btn btn-link btn-sm p-0 text-muted"
                          @click="toggleTimeline(a.id)">
                    {{ openTimelines.includes(a.id)
                      ? 'Hide timeline ▲'
                      : `Status timeline (${parsedHistory(a).length} changes) ▼` }}
                  </button>
                  <div v-if="openTimelines.includes(a.id)"
                       class="mt-2 ps-2 border-start border-2"
                       style="border-color:var(--color-border-secondary)!important">
                    <div v-for="(h, idx) in parsedHistory(a)" :key="idx"
                         class="d-flex gap-2 align-items-start mb-1 small">
                      <span class="badge" :class="appBadge(h.to)">{{ h.to }}</span>
                      <span class="text-muted">{{ formatDateTime(h.timestamp) }}</span>
                      <span v-if="h.remarks" class="text-muted">· {{ h.remarks }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../api'
import ExportButton from '../../components/ExportButton.vue'

export default {
  name: 'StudentHistoryView',
  components: { ExportButton },
  data() {
    return {
      data: {}, loading: true,
      activeTab: 'all', search: '',
      openTimelines: [],
      tabs: [
        { label: 'All',         value: 'all'         },
        { label: 'Active',      value: 'active'      },
        { label: 'Interview',   value: 'interview'   },
        { label: 'Offer',       value: 'offer'       },
        { label: 'Placed',      value: 'placed'      },
        { label: 'Rejected',    value: 'rejected'    },
      ],
    }
  },
  computed: {
    history() { return this.data.history || [] },
    summary() { return this.data.summary || {} },
    summaryCards() {
      return [
        { label: 'Total',       value: this.summary.total       || 0, color: 'text-primary'   },
        { label: 'Shortlisted', value: this.summary.shortlisted || 0, color: 'text-info'      },
        { label: 'Interview',   value: this.summary.interview   || 0, color: 'text-warning'   },
        { label: 'Offer',       value: this.summary.offer       || 0, color: 'text-primary'   },
        { label: 'Placed',      value: this.summary.placed      || 0, color: 'text-success'   },
        { label: 'Rejected',    value: this.summary.rejected    || 0, color: 'text-danger'    },
      ]
    },
    filtered() {
      let list = this.history
      if (this.search.trim()) {
        const q = this.search.toLowerCase()
        list = list.filter(a =>
          a.company_name?.toLowerCase().includes(q) ||
          a.job_title?.toLowerCase().includes(q)
        )
      }
      if (this.activeTab === 'all') return list
      if (this.activeTab === 'active') {
        return list.filter(a =>
          ['applied','shortlisted','interview','waiting','offer'].includes(a.status))
      }
      if (this.activeTab === 'placed') {
        return list.filter(a => ['selected','placed'].includes(a.status))
      }
      return list.filter(a => a.status === this.activeTab)
    },
  },
  async created() {
    try {
      const { data } = await api.get('/student/history')
      this.data = data
    } finally { this.loading = false }
  },
  methods: {
    parsedHistory(a) {
      try { return JSON.parse(a.status_history || '[]') }
      catch { return [] }
    },
    toggleTimeline(id) {
      const idx = this.openTimelines.indexOf(id)
      if (idx === -1) this.openTimelines.push(id)
      else this.openTimelines.splice(idx, 1)
    },
    exportCSV() {
      const rows = [
        ['Student Name', 'Company', 'Job Title', 'Job Type',
         'Applied On', 'Status', 'Interview Type', 'Interview Date',
         'Remarks', 'Placed', 'Salary', 'Joining Date'],
        ...this.filtered.map(a => [
          this.data.student?.full_name || '',
          a.company_name || '',
          a.job_title || '',
          a.drive?.job_type || '',
          this.formatDate(a.applied_at),
          a.status,
          a.interview_type || '',
          a.interview_date ? this.formatDateTime(a.interview_date) : '',
          (a.remarks || '').replace(/,/g, ';'),
          a.placement ? 'Yes' : 'No',
          a.placement?.salary || '',
          a.placement?.joining_date || '',
        ]),
      ]
      const csv  = rows.map(r => r.join(',')).join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      const url  = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href     = url
      link.download = `placement_history_${this.data.student?.full_name || 'student'}.csv`
      link.click()
      URL.revokeObjectURL(url)
    },
    statusLabel(s) {
      return {
        applied: 'Applied', shortlisted: 'Shortlisted',
        interview: 'Interview', waiting: 'Waiting',
        offer: 'Offer Received', selected: 'Selected',
        placed: 'Placed', rejected: 'Rejected',
      }[s] || s
    },
    statusInitial(s) {
      return {
        applied: 'AP', shortlisted: 'SL', interview: 'IN',
        waiting: 'WT', offer: 'OF', selected: 'SE',
        placed: 'PL', rejected: 'RJ',
      }[s] || '?'
    },
    statusColor(s) {
      return {
        applied: '#6c757d', shortlisted: '#0dcaf0',
        interview: '#fd7e14', waiting: '#ffc107',
        offer: '#0d6efd', selected: '#198754',
        placed: '#20c997', rejected: '#dc3545',
      }[s] || '#6c757d'
    },
    appBadge(s) {
      return {
        applied: 'bg-secondary', shortlisted: 'bg-info text-dark',
        interview: 'bg-warning text-dark', waiting: 'bg-warning text-dark',
        offer: 'bg-primary', selected: 'bg-success',
        placed: 'bg-success', rejected: 'bg-danger',
      }[s] || 'bg-secondary'
    },
    formatDate(d) {
      return d ? new Date(d).toLocaleDateString('en-IN') : '—'
    },
    formatDateTime(d) {
      return d ? new Date(d).toLocaleString('en-IN',
        { dateStyle: 'medium', timeStyle: 'short' }) : '—'
    },
  },
}
</script>
