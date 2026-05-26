export const SOURCES = [
  {
    id: 'sap_fuel',
    label: 'SAP Fuel & Procurement',
    shortLabel: 'SAP',
    scope: 'Scope 1',
    description: 'MB51 material document export — fuel combustion and procurement.',
    samplePath: '/samples/sap_fuel.csv',
    sampleDownloadName: 'sap_fuel_sample.csv',
    accent: 'emerald',
  },
  {
    id: 'electricity',
    label: 'Electricity',
    shortLabel: 'Utility',
    scope: 'Scope 2',
    description: 'Utility portal usage history — kWh consumption by billing period.',
    samplePath: '/samples/electricity.csv',
    sampleDownloadName: 'electricity_sample.csv',
    accent: 'sky',
  },
  {
    id: 'travel',
    label: 'Corporate Travel',
    shortLabel: 'Travel',
    scope: 'Scope 3',
    description: 'Concur-style trip report — flights, hotels, and ground transport.',
    samplePath: '/samples/travel.csv',
    sampleDownloadName: 'travel_sample.csv',
    accent: 'violet',
  },
]

export const SOURCE_BY_ID = Object.fromEntries(SOURCES.map((s) => [s.id, s]))

export const STATUS_OPTIONS = [
  { id: 'pending', label: 'Pending', description: 'Passed checks — ready for approval' },
  { id: 'flagged', label: 'Flagged', description: 'Needs analyst review' },
  { id: 'approved', label: 'Approved', description: 'Locked for audit' },
  { id: 'rejected', label: 'Rejected', description: 'Excluded from totals' },
]

export const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'upload', label: 'Ingest data' },
  { id: 'review', label: 'Review records' },
]
