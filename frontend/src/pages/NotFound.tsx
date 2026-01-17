/**
 * 404 Not Found page.
 *
 * Displayed when a user navigates to a route that doesn't exist.
 */

import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <CardTitle className="text-6xl font-bold text-muted-foreground">404</CardTitle>
          <CardDescription className="text-lg">Page Not Found</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            The page you're looking for doesn't exist or has been moved.
          </p>
          <div className="flex gap-4 justify-center">
            <Button asChild>
              <Link to="/">Go to Budget</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/accounts">View Accounts</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default NotFound
