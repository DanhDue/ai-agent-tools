/**
 * TypeScript Data Models & Contract Specifications for Antigravity Quota Dashboard.
 * 
 * Color Thresholds:
 *   >= 50%           : Emerald Green (#10b981 / #72bc82)
 *   >= 10% and < 50% : Amber Orange  (#f59e0b)
 *   < 10%            : Crimson Red   (#ef4444)
 */

export type QuotaWindow = '5h' | 'weekly';

export type StatusColor = 'green' | 'amber' | 'red' | 'gray';

export type AccountStatus = 'ACTIVE' | 'EXHAUSTED' | 'AUTH NEEDED' | 'DISABLED';

export type ArgonMode = 'separate' | 'shared_gemini' | 'none';

export interface ModelCatalogEntry {
  id: string;
  label?: string;
  quotaFamily: 'gemini' | 'claude' | 'argon' | 'other';
  tags: string[];
}

export interface ProfileCapabilities {
  tier: string;
  hasCarbon: boolean;
  hasArgon: boolean;
  argonMode: ArgonMode;
  hasOrchestrator: boolean;
  badges: string[];
}

export interface QuotaBucket {
  name: string;
  fraction: number;         // 0.0 to 1.0 remaining
  countdown: string;
  resetTime: string;        // ISO 8601 UTC timestamp
  resetTimeLocal?: string;
  unavailable: boolean;
  tags?: boolean | string[];
  sharedPool?: boolean;
  mode?: ArgonMode;
  id?: string;
  window?: QuotaWindow;
  remainingFraction?: number; // Legacy alias (0.0 to 1.0)
  description?: string;
  isAvailable?: boolean;    // Legacy alias: false if model is inactive / unavailable
}

export interface QuotaGroup {
  name: string;
  description: string;
  buckets: QuotaBucket[];
  models?: string[];
}

export interface DynamicQuotaShareInfo {
  limitIndex?: number | null;
  usedPercentOfWeekly?: number | null;
  allowancePercentOfWeekly?: number | null;
  label: string;
}

export interface DynamicQuotaBucket {
  id: string;
  name: string;
  group: 'session' | 'weekly' | string;
  kind: string;
  scopeLabel: string;
  fraction: number;         // 0.0 to 1.0 remaining
  utilization: number;      // 0.0 to 100.0 used
  countdown: string;
  resetTime: string;        // ISO 8601 UTC timestamp
  resetTimeLocal: string;
  resetTimeTs?: number;
  severity: string;
  isActive: boolean;
  isLive: boolean;
  shareInfo?: DynamicQuotaShareInfo | null;
  unavailable: boolean;
}

export interface AccountMeta {
  provider: 'antigravity' | 'claude' | 'codex' | 'kiro' | string;
  vendorLabel: string;
  planType: string;
  planLabel: string;
  userTier?: string;
  tierDisplayName?: string;
  authMethod?: string;
  upgradeText?: string;
  upgradeUrl?: string;
  remainingCredits?: number;
  organizationName?: string;
  organizationType?: string;
  billingType?: string;
  rateLimitTier?: string;
  authSource?: string;
  cliCommand?: string;
  configPath?: string;
  secondaryPath?: string;
  extraUsageEnabled?: boolean;
  extraUsageSummary?: string;
  resetCredits?: number;
  creditsSummary?: string;
  overageStatus?: string;
  overageRateSummary?: string;
}

export interface ProfileQuotaState {
  profile: string;
  email?: string;
  tier: 'ULTRA' | 'PRO' | 'FREE' | string;
  planLabel?: string;
  vendorLabel?: string;
  priority?: number;        // Default: 50
  hasArgon?: boolean;       // Display ✣ Argon tag if argonMode !== 'none'
  status: AccountStatus;
  gemini5h: QuotaBucket;
  geminiWeekly: QuotaBucket;
  claude5h: QuotaBucket;
  claudeWeekly: QuotaBucket;
  argon5h?: QuotaBucket;
  argonWeekly: QuotaBucket;
  quotaBuckets?: DynamicQuotaBucket[];
  availableModels?: string[];
  modelCatalog?: ModelCatalogEntry[];
  groupModels?: { gemini: string[]; claude: string[]; argon: string[] };
  capabilities?: ProfileCapabilities;
  accountMeta?: AccountMeta;
  modelsFetchedAt?: string;
  groupDescSig?: string;
}

/**
 * Maps quota percentage to strict color category.
 */
export function getStatusColor(pct: number): StatusColor {
  if (pct >= 50.0) return 'green';
  if (pct >= 10.0) return 'amber';
  return 'red';
}

/**
 * Calculates human-readable countdown remaining until full quota reset.
 */
export function formatResetCountdown(resetTimeIso: string): string {
  if (!resetTimeIso) return '⏱ --';
  try {
    const target = new Date(resetTimeIso);
    const now = new Date();
    const diffMs = Math.max(0, target.getTime() - now.getTime());
    const totalSecs = Math.floor(diffMs / 1000);
    const days = Math.floor(totalSecs / 86400);
    const hours = Math.floor((totalSecs % 86400) / 3600);
    const minutes = Math.floor((totalSecs % 3600) / 60);

    if (days > 0) return `⏱ ${days}d ${hours}h`;
    if (hours > 0) return `⏱ ${hours}h ${minutes}m`;
    if (minutes > 0) return `⏱ ${minutes}m`;
    return '⏱ Ready';
  } catch {
    return '⏱ --';
  }
}

