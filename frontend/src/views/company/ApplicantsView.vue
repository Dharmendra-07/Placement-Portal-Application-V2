<template>
  <div class="container-fluid py-4 px-4">

    <!-- Back + heading -->
    <div class="d-flex align-items-center gap-3 mb-4 flex-wrap">
      <button class="btn btn-sm btn-outline-secondary"
              @click="$router.back()">← Back</button>
      <div>
        <h5 class="fw-bold mb-0">{{ drive?.job_title || 'Drive Applicants' }}</h5>
        <span class="text-muted small" v-if="drive">
          {{ drive.job_type }} · {{ drive.location || 'Remote' }} ·
          Deadline: {{ formatDate(drive.application_deadline) }}
        </span>
      </div>
      <span class="badge ms-auto"
            :class="drive ? statusBadge(drive.status) : 'bg-secondary'">
        {{ drive?.status }}
      </span>
    </div>

    <!-- Status filter tabs + bulk action bar -->
    <div class="d-flex align-items-center gap-2 mb-3 flex-wrap">
      <div class="d-flex gap-1 flex-wrap">
        <button v-for="tab in tabs" :key="tab.value"
                class="btn btn-sm"
                :class="activeTab === tab.value
                  ? 'btn-primary' : 'btn-outline-secondary'"
                @click="activeTab = tab.value; selected = []">
          {{ tab.label }}
          <span class="badge ms-1"
                :class="activeTab === tab.value
                  ? 'bg-white text-primary' : 'bg-secondary'">
            {{ countByStatus(tab.value) }}
          </span>
        </button>
      </div>

      <!-- Bulk actions (show only when rows are selected) -->
      <div v-if="selected.length" class="d-flex gap-2 ms-auto align-items-center">
        <span class="text-muted small">{{ selected.length }} selected</span>
        <select v-model="bulkStatus" class="form-select form-select-sm"
                style="width:140px">
          <option value="">Set status…</option>
          <option value="shortlisted">Shortlist</option>
          <option value="waiting">Waiting</option>
          <option value="selected">Select</option>
          <option value="rejected">Reject</option>
        </select>
        <button class="btn btn-sm btn-primary"
                :disabled="!bulkStatus || bulkLoading"
                @click="applyBulk">
          <span v-if="bulkLoading"
                class="spinner-border spinner-border-sm me-1"></span>
          Apply
        </button>
      </div>
    </div>

    <!-- Table -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else-if="filteredApps.length === 0"
         class="text-muted text-center py-5">
      No applications in this category.
    </div>

    <div v-else>
      <div class="table-responsive">
        <table class="table table-hover align-middle">
          <thead class="table-light">
            <tr>
              <th style="width:36px">
                <input type="checkbox" @change="toggleAll"
                       :checked="allSelected" />
              </th>
              <th>Student</th>
              <th>Dept</th>
              <th>CGPA</th>
              <th>Applied on</th>
              <th>Interview</th>
              <th>Status</th>
              <th style="width:220px">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in filteredApps" :key="a.id">
              <td>
                <input type="checkbox"
                       :value="a.id"
                       v-model="selected" />
              </td>
              <td>
                <div class="fw-medium">{{ a.student_name }}</div>
                <a v-if="a.student_detail?.resume_url"
                   :href="a.student_detail.resume_url"
                   target="_blank"
                   class="text-decoration-none small text-primary">
                  View resume
                </a>
              </td>
              <td class="small">{{ a.student_dept || '—' }}</td>
              <td class="small fw-medium">{{ a.student_cgpa || '—' }}</td>
              <td class="small">{{ formatDate(a.applied_at) }}</td>
              <td class="small">
                <div v-if="a.interview_date">
                  <div>{{ a.interview_type }}</div>
                  <div class="text-muted">{{ formatDate(a.interview_date) }}</div>
                </div>
                <span v-else class="text-muted">—</span>
              </td>
              <td>
                <span class="badge" :class="appBadge(a.status)">
                  {{ a.status }}
                </span>
                <div v-if="a.remarks"
                     class="text-muted mt-1" style="font-size:11px">
                  {{ a.remarks }}
                </div>
              </td>
              <td>
                <div class="d-flex gap-1 flex-wrap">
                  <!-- Quick status buttons -->
                  <button v-if="a.status !== 'shortlisted'"
                          class="btn btn-sm btn-outline-info"
                          @click="quickStatus(a.id, 'shortlisted')">
                    Shortlist
                  </button>
                  <button v-if="a.status !== 'selected'"
                          class="btn btn-sm btn-outline-success"
                          @click="quickStatus(a.id, 'selected')">
                    Select
                  </button>
                  <button v-if="a.status !== 'rejected'"
                          class="btn btn-sm btn-outline-danger"
                          @click="quickStatus(a.id, 'rejected')">
                    Reject
                  </button>
                  <!-- Schedule interview -->
                  <button class="btn btn-sm btn-outline-secondary"
                          @click="openSchedule(a)">
                    Schedule
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Schedule interview modal (inline panel) ── -->
    <div v-if="scheduleApp" class="card border-0 shadow-sm mt-4">
      <div class="card-header bg-white fw-semibold d-flex justify-content-between">
        Schedule Interview — {{ scheduleApp.student_name }}
        <button class="btn-close" @click="scheduleApp = null"></button>
      </div>
      <div class="card-body">
        <div v-if="scheduleError"
             class="alert alert-danger py-2 small mb-3">
          {{ scheduleError }}
        </div>
        <div class="row g-3">
          <div class="col-md-4">
            <label class="form-label small fw-medium">Interview type</label>
            <select v-model="scheduleForm.interview_type" class="form-select">
              <option>In-person</option>
              <option>Virtual</option>
              <option>Phone</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label small fw-medium">
              Date & time <span class="text-danger">*</span>
            </label>
            <input v-model="scheduleForm.interview_date"
                   type="datetime-local" class="form-control" />
          </div>
          <div class="col-md-4">
            <label class="form-label small fw-medium">Remarks / venue</label>
            <input v-model="scheduleForm.remarks" type="text"
                   class="form-control" placeholder="Zoom link, room no..." />
          </div>
        </div>
        <button class="btn btn-primary mt-3"
                :disabled="scheduleLoading"
                @click="saveSchedule">
          <span v-if="scheduleLoading"
                class="spinner-border spinner-border-sm me-1"></span>
          Confirm Schedule
        </button>
      </div>
    </div>

  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'CompanyApplicantsView',
  data() {
    return {
      applications: [],
      drive: null,
      loading: true,
      activeTab: 'all',
      tabs: [
        { label: 'All',         value: 'all'         },
        { label: 'Applied',     value: 'applied'     },
        { label: 'Shortlisted', value: 'shortlisted' },
        { label: 'Waiting',     value: 'waiting'     },
        { label: 'Selected',    value: 'selected'    },
        { label: 'Rejected',    value: 'rejected'    },
      ],
      selected: [],
      bulkStatus: '',
      bulkLoading: false,
      scheduleApp: null,
      scheduleForm: { interview_type: 'In-person', interview_date: '', remarks: '' },
      scheduleError: '',
      scheduleLoading: false,
    }
  },
  computed: {
    filteredApps() {
      if (this.activeTab === 'all') return this.applications
      return this.applications.filter(a => a.status === this.activeTab)
    },
    allSelected() {
      return this.filteredApps.length > 0 &&
        this.filteredApps.every(a => this.selected.includes(a.id))
    },
  },
  created() { this.fetchData() },
  methods: {
    async fetchData() {
      this.loading = true
      const id = this.$route.params.driveId
      try {
        const [driveRes, appsRes] = await Promise.all([
          api.get(`/company/drives/${id}`),
          api.get(`/company/drives/${id}/applications`),
        ])
        this.drive        = driveRes.data
        this.applications = appsRes.data
      } finally { this.loading = false }
    },
    countByStatus(status) {
      if (status === 'all') return this.applications.length
      return this.applications.filter(a => a.status === status).length
    },
    toggleAll(e) {
      this.selected = e.target.checked
        ? this.filteredApps.map(a => a.id) : []
    },
    async quickStatus(appId, status) {
      try {
        await api.put(`/company/applications/${appId}/status`, { status })
        await this.fetchData()
      } catch (err) {
        alert(err.response?.data?.message || 'Update failed.')
      }
    },
    async applyBulk() {
      if (!this.bulkStatus || !this.selected.length) return
      this.bulkLoading = true
      try {
        const id = this.$route.params.driveId
        await api.put(`/company/drives/${id}/applications/bulk`, {
          application_ids: this.selected,
          status: this.bulkStatus,
        })
        this.selected   = []
        this.bulkStatus = ''
        await this.fetchData()
      } catch (err) {
        alert(err.response?.data?.message || 'Bulk update failed.')
      } finally { this.bulkLoading = false }
    },
    openSchedule(app) {
      this.scheduleApp   = app
      this.scheduleError = ''
      this.scheduleForm  = {
        interview_type: app.interview_type || 'In-person',
        interview_date: app.interview_date
          ? app.interview_date.slice(0, 16) : '',
        remarks: app.remarks || '',
      }
    },
    async saveSchedule() {
      this.scheduleError = ''
      if (!this.scheduleForm.interview_date) {
        this.scheduleError = 'Interview date is required.'
        return
      }
      this.scheduleLoading = true
      try {
        await api.put(
          `/company/applications/${this.scheduleApp.id}/schedule`,
          this.scheduleForm
        )
        this.scheduleApp = null
        await this.fetchData()
      } catch (err) {
        this.scheduleError =
          err.response?.data?.message || 'Failed to schedule interview.'
      } finally { this.scheduleLoading = false }
    },
    appBadge(s) {
      return {
        applied:     'bg-secondary',
        shortlisted: 'bg-info text-dark',
        selected:    'bg-success',
        rejected:    'bg-danger',
        waiting:     'bg-warning text-dark',
      }[s] || 'bg-secondary'
    },
    statusBadge(s) {
      return {
        pending:  'bg-warning text-dark',
        approved: 'bg-success',
        closed:   'bg-secondary',
      }[s] || 'bg-secondary'
    },
    formatDate(d) {
      return d ? new Date(d).toLocaleDateString('en-IN') : '—'
    },
  },
}
</script>
