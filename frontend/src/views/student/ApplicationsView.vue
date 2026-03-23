<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">My Applications</h5>

    <!-- Status filter tabs -->
    <div class="d-flex gap-1 flex-wrap mb-3">
      <button v-for="tab in tabs" :key="tab.value"
              class="btn btn-sm"
              :class="activeTab === tab.value
                ? 'btn-primary' : 'btn-outline-secondary'"
              @click="activeTab = tab.value">
        {{ tab.label }}
        <span class="badge ms-1"
              :class="activeTab === tab.value
                ? 'bg-white text-primary' : 'bg-secondary'">
          {{ countByStatus(tab.value) }}
        </span>
      </button>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else-if="filteredApps.length === 0"
         class="text-muted text-center py-5">
      No applications in this category.
    </div>

    <div v-else class="row g-3">
      <div class="col-md-6 col-lg-4" v-for="a in filteredApps" :key="a.id">
        <div class="card border-0 shadow-sm h-100">
          <!-- Coloured top bar by status -->
          <div class="card-header border-0 py-2"
               :style="`background:${statusColor(a.status)};
                        border-radius:var(--bs-border-radius-lg)
                        var(--bs-border-radius-lg) 0 0`">
            <div class="d-flex justify-content-between align-items-center">
              <span class="badge" :class="appBadge(a.status)">{{ a.status }}</span>
              <span class="text-white small opacity-75">
                Applied {{ formatDate(a.applied_at) }}
              </span>
            </div>
          </div>

          <div class="card-body">
            <h6 class="fw-bold mb-1">{{ a.job_title }}</h6>
            <p class="text-primary small fw-medium mb-2">{{ a.company_name }}</p>

            <!-- Interview info -->
            <div v-if="a.interview_date"
                 class="alert alert-info py-2 px-3 small mb-2">
              <div class="fw-medium">Interview Scheduled</div>
              <div>{{ a.interview_type }} · {{ formatDateTime(a.interview_date) }}</div>
              <div v-if="a.remarks" class="text-muted mt-1">{{ a.remarks }}</div>
            </div>

            <!-- Remarks/feedback -->
            <div v-else-if="a.remarks"
                 class="text-muted small border-start border-3 ps-2 mb-2"
                 :style="`border-color:${statusColor(a.status)} !important`">
              {{ a.remarks }}
            </div>
          </div>

          <div class="card-footer bg-transparent d-flex gap-2">
            <button class="btn btn-sm btn-outline-secondary flex-fill"
                    @click="viewDetail(a.id)">
              View Details
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Detail modal (inline panel) ── -->
    <div v-if="detail" class="card border-0 shadow-sm mt-4">
      <div class="card-header bg-white fw-semibold
                  d-flex justify-content-between align-items-center">
        Application Detail
        <button class="btn-close" @click="detail = null"></button>
      </div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-6">
            <p class="mb-1"><span class="text-muted small">Company</span></p>
            <p class="fw-medium">{{ detail.company_name }}</p>
          </div>
          <div class="col-md-6">
            <p class="mb-1"><span class="text-muted small">Job Title</span></p>
            <p class="fw-medium">{{ detail.job_title }}</p>
          </div>
          <div class="col-md-4">
            <p class="mb-1"><span class="text-muted small">Status</span></p>
            <span class="badge fs-6 fw-normal"
                  :class="appBadge(detail.status)">{{ detail.status }}</span>
          </div>
          <div class="col-md-4">
            <p class="mb-1"><span class="text-muted small">Applied on</span></p>
            <p>{{ formatDate(detail.applied_at) }}</p>
          </div>
          <div class="col-md-4" v-if="detail.student_dept">
            <p class="mb-1"><span class="text-muted small">Department</span></p>
            <p>{{ detail.student_dept }}</p>
          </div>

          <!-- Drive details -->
          <template v-if="detail.drive_detail">
            <div class="col-12"><hr class="my-1"></div>
            <div class="col-md-4">
              <p class="mb-1"><span class="text-muted small">Salary</span></p>
              <p>
                {{ detail.drive_detail.salary_min
                   ? `₹${detail.drive_detail.salary_min}–${detail.drive_detail.salary_max} LPA`
                   : '—' }}
              </p>
            </div>
            <div class="col-md-4">
              <p class="mb-1"><span class="text-muted small">Location</span></p>
              <p>{{ detail.drive_detail.location || 'Remote' }}</p>
            </div>
            <div class="col-md-4">
              <p class="mb-1"><span class="text-muted small">Job type</span></p>
              <p>{{ detail.drive_detail.job_type }}</p>
            </div>
          </template>

          <!-- Interview -->
          <template v-if="detail.interview_date">
            <div class="col-12"><hr class="my-1"></div>
            <div class="col-12">
              <p class="mb-1 fw-medium">Interview Details</p>
            </div>
            <div class="col-md-4">
              <p class="mb-1"><span class="text-muted small">Type</span></p>
              <p>{{ detail.interview_type }}</p>
            </div>
            <div class="col-md-4">
              <p class="mb-1"><span class="text-muted small">Date & time</span></p>
              <p>{{ formatDateTime(detail.interview_date) }}</p>
            </div>
            <div class="col-md-4" v-if="detail.remarks">
              <p class="mb-1"><span class="text-muted small">Remarks / venue</span></p>
              <p>{{ detail.remarks }}</p>
            </div>
          </template>

          <!-- Placement / offer letter -->
          <template v-if="detail.placement">
            <div class="col-12"><hr class="my-1"></div>
            <div class="col-12">
              <div class="alert alert-success mb-0">
                <div class="fw-medium mb-1">Placement Confirmed</div>
                <div class="small">
                  Position: {{ detail.placement.position }} ·
                  Salary: ₹{{ detail.placement.salary }} LPA ·
                  Joining: {{ detail.placement.joining_date || 'TBD' }}
                </div>
                <a v-if="detail.placement.offer_letter_url"
                   :href="detail.placement.offer_letter_url"
                   target="_blank"
                   class="btn btn-sm btn-success mt-2">
                  Download Offer Letter
                </a>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'StudentApplicationsView',
  data() {
    return {
      applications: [], loading: true,
      activeTab: 'all',
      detail: null,
      tabs: [
        { label: 'All',         value: 'all'         },
        { label: 'Applied',     value: 'applied'     },
        { label: 'Shortlisted', value: 'shortlisted' },
        { label: 'Waiting',     value: 'waiting'     },
        { label: 'Selected',    value: 'selected'    },
        { label: 'Rejected',    value: 'rejected'    },
      ],
    }
  },
  computed: {
    filteredApps() {
      if (this.activeTab === 'all') return this.applications
      return this.applications.filter(a => a.status === this.activeTab)
    },
  },
  async created() {
    try {
      const { data } = await api.get('/student/applications')
      this.applications = data
    } finally { this.loading = false }
  },
  methods: {
    countByStatus(status) {
      if (status === 'all') return this.applications.length
      return this.applications.filter(a => a.status === status).length
    },
    async viewDetail(appId) {
      const { data } = await api.get(`/student/applications/${appId}`)
      this.detail = data
      this.$nextTick(() => {
        document.querySelector('.card.border-0.shadow-sm.mt-4')
          ?.scrollIntoView({ behavior: 'smooth' })
      })
    },
    appBadge(s) {
      return {
        applied: 'bg-secondary', shortlisted: 'bg-info text-dark',
        selected: 'bg-success',  rejected: 'bg-danger',
        waiting:  'bg-warning text-dark',
      }[s] || 'bg-secondary'
    },
    statusColor(s) {
      return {
        applied: '#6c757d', shortlisted: '#0dcaf0',
        selected: '#198754', rejected: '#dc3545',
        waiting:  '#ffc107',
      }[s] || '#6c757d'
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
