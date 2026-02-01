import { useState, useEffect } from 'react'
import { LayoutGrid, Wallet, ArrowLeftRight } from 'lucide-react'
import { useLocation, Link } from 'react-router-dom'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarGroup,
  SidebarGroupContent,
} from '@/components/ui/sidebar'
import { Badge } from '@/components/ui/badge'
import { NavUser } from './NavUser'
import { transactionService } from '@/services/transactionService'

const navItems = [
  {
    title: 'Budget',
    url: '/budget',
    icon: LayoutGrid,
  },
  {
    title: 'Accounts',
    url: '/accounts',
    icon: Wallet,
  },
  {
    title: 'Transactions',
    url: '/transactions',
    icon: ArrowLeftRight,
  },
]

export function AppSidebar() {
  const location = useLocation()
  const [uncategorizedCount, setUncategorizedCount] = useState(0)

  useEffect(() => {
    const fetchUncategorizedCount = async () => {
      try {
        const response = await transactionService.listInbox({ limit: 0 })
        setUncategorizedCount(response.total)
      } catch {
        // Don't show badge if fetch fails
        setUncategorizedCount(0)
      }
    }

    fetchUncategorizedCount()
    const interval = setInterval(fetchUncategorizedCount, 30000)

    // Listen for account deletion events to refresh count
    const handleAccountDeleted = () => fetchUncategorizedCount()
    window.addEventListener('account-deleted', handleAccountDeleted)

    return () => {
      clearInterval(interval)
      window.removeEventListener('account-deleted', handleAccountDeleted)
    }
  }, [])

  const isActive = (url: string) => {
    if (url === '/budget') {
      return location.pathname === '/' || location.pathname === '/budget'
    }
    return location.pathname === url
  }

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link to="/budget">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <LayoutGrid className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold">MyBudget</span>
                  <span className="text-xs text-muted-foreground">Spending Targets</span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={isActive(item.url)}
                    tooltip={item.title}
                  >
                    <Link to={item.url} className="flex items-center justify-between w-full">
                      <div className="flex items-center gap-2">
                        <item.icon />
                        <span>{item.title}</span>
                      </div>
                      {item.title === 'Transactions' && uncategorizedCount > 0 && (
                        <Badge variant="destructive" className="ml-auto">
                          {uncategorizedCount}
                        </Badge>
                      )}
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
