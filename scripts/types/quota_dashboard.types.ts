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

export type AccountStatus = 'ACTIVE' | 'EXHAUSTED' | 'AUTH NEEDED';

export interface QuotaBucket {
  id: string;
  name: string;
  window: QuotaWindow;
  remainingFraction: number; // 0.0 to 1.0
  resetTime: string;        // ISO 8601 UTC timestamp
  description?: string;
  isAvailable?: boolean;    // false if model is inactive / unavailable (e.g. Argon on tess)
}

export interface QuotaGroup {
  name: string;
  description: string;
  buckets: QuotaBucket[];
}

export interface ProfileQuotaState {
  profile: string;
  tier: 'PRO' | 'DEV' | string;
  priority?: number;        // Default: 50
  hasArgon?: boolean;       // Display ✣ Argon tag if present
  status: AccountStatus;
  gemini5h: QuotaBucket;
  geminiWeekly: QuotaBucket;
  claude5h: QuotaBucket;
  claudeWeekly: QuotaBucket;
  argon5h?: QuotaBucket;
  argonWeekly: QuotaBucket;
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

