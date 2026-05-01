import type { RouteType } from '../types'

type RouteBadgeProps = {
  route: RouteType | null
}

export function RouteBadge({ route }: RouteBadgeProps) {
  const normalized = (route ?? 'unknown').toString().toUpperCase()
  const tone = normalized.toLowerCase()

  return <span className={`route-badge route-${tone}`}>{normalized}</span>
}

