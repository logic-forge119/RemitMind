import * as React from "react"
import { motion } from "framer-motion"
import { ArrowRight, Eye, EyeOff, Compass } from "lucide-react"

// Utility helper
function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ")
}

// Button Component
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline"
  children: React.ReactNode
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, variant = "default", className = "", ...props }, ref) => {
    const base = "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
    const variants = {
      default: "bg-primary bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:from-blue-600 hover:to-indigo-700",
      outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground"
    }
    return (
      <button ref={ref} className={cn(base, variants[variant], className)} {...props}>
        {children}
      </button>
    )
  }
)
Button.displayName = "Button"

// Input Component
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", type, ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        className={cn(
          "flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm text-gray-800 dark:text-gray-100 ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

// World Map Canvas Animation Component
const WorldMap = () => {
  const canvasRef = React.useRef<HTMLCanvasElement>(null)
  const [dimensions, setDimensions] = React.useState({ width: 0, height: 0 })

  const routes = [
    { start: { x: 100, y: 150, delay: 0 }, end: { x: 200, y: 80, delay: 2 }, color: "#2563eb" },
    { start: { x: 200, y: 80, delay: 2 }, end: { x: 260, y: 120, delay: 4 }, color: "#2563eb" },
    { start: { x: 50, y: 50, delay: 1 }, end: { x: 150, y: 180, delay: 3 }, color: "#2563eb" },
    { start: { x: 280, y: 60, delay: 0.5 }, end: { x: 180, y: 180, delay: 2.5 }, color: "#2563eb" }
  ]

  const generateContinentDots = (w: number, h: number) => {
    const dots: Array<{ x: number; y: number; radius: number; opacity: number }> = []
    for (let x = 0; x < w; x += 12) {
      for (let y = 0; y < h; y += 12) {
        const inNA = x < w * 0.25 && x > w * 0.05 && y < h * 0.4 && y > h * 0.1
        const inSA = x < w * 0.25 && x > w * 0.15 && y < h * 0.8 && y > h * 0.4
        const inEU = x < w * 0.45 && x > w * 0.3 && y < h * 0.35 && y > h * 0.15
        const inAF = x < w * 0.5 && x > w * 0.35 && y < h * 0.65 && y > h * 0.35
        const inAS = x < w * 0.7 && x > w * 0.45 && y < h * 0.5 && y > h * 0.1
        const inAU = x < w * 0.8 && x > w * 0.65 && y < h * 0.8 && y > h * 0.6

        if ((inNA || inSA || inEU || inAF || inAS || inAU) && Math.random() > 0.3) {
          dots.push({
            x,
            y,
            radius: 1,
            opacity: Math.random() * 0.5 + 0.2
          })
        }
      }
    }
    return dots
  }

  React.useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ro = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect
      setDimensions({ width, height })
      canvas.width = width
      canvas.height = height
    })
    ro.observe(canvas.parentElement!)
    return () => ro.disconnect()
  }, [])

  React.useEffect(() => {
    if (!dimensions.width || !dimensions.height) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const dots = generateContinentDots(dimensions.width, dimensions.height)
    let animId: number
    let startTime = Date.now()

    function drawDots() {
      ctx!.clearRect(0, 0, dimensions.width, dimensions.height)
      dots.forEach((dot) => {
        ctx!.beginPath()
        ctx!.arc(dot.x, dot.y, dot.radius, 0, Math.PI * 2)
        ctx!.fillStyle = `rgba(37, 99, 235, ${dot.opacity})`
        ctx!.fill()
      })
    }

    function drawRoutes() {
      const elapsed = (Date.now() - startTime) / 1000
      routes.forEach((route) => {
        const time = elapsed - route.start.delay
        if (time <= 0) return
        const progress = Math.min(time / 3, 1)
        const currentX = route.start.x + (route.end.x - route.start.x) * progress
        const currentY = route.start.y + (route.end.y - route.start.y) * progress

        ctx!.beginPath()
        ctx!.moveTo(route.start.x, route.start.y)
        ctx!.lineTo(currentX, currentY)
        ctx!.strokeStyle = route.color
        ctx!.lineWidth = 1.5
        ctx!.stroke()

        ctx!.beginPath()
        ctx!.arc(route.start.x, route.start.y, 3, 0, Math.PI * 2)
        ctx!.fillStyle = route.color
        ctx!.fill()

        ctx!.beginPath()
        ctx!.arc(currentX, currentY, 3, 0, Math.PI * 2)
        ctx!.fillStyle = "#3b82f6"
        ctx!.fill()

        ctx!.beginPath()
        ctx!.arc(currentX, currentY, 6, 0, Math.PI * 2)
        ctx!.fillStyle = "rgba(59, 130, 246, 0.4)"
        ctx!.fill()

        if (progress === 1) {
          ctx!.beginPath()
          ctx!.arc(route.end.x, route.end.y, 3, 0, Math.PI * 2)
          ctx!.fillStyle = route.color
          ctx!.fill()
        }
      })
    }

    function loop() {
      drawDots()
      drawRoutes()
      if ((Date.now() - startTime) / 1000 > 15) {
        startTime = Date.now()
      }
      animId = requestAnimationFrame(loop)
    }

    loop()
    return () => cancelAnimationFrame(animId)
  }, [dimensions])

  return (
    <div className="relative w-full h-full overflow-hidden">
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
    </div>
  )
}

// Main Travel Connect Signin Component
export default function TravelConnectSignin1() {
  const [showPassword, setShowPassword] = React.useState(false)
  const [email, setEmail] = React.useState("gajiulislam@gmail.com")
  const [password, setPassword] = React.useState("password123")
  const [isHovered, setIsHovered] = React.useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log("Sign in attempt with:", { email, password })
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 p-4">
      <div className="max-w-4xl w-full bg-white dark:bg-gray-900 rounded-2xl shadow-xl overflow-hidden flex flex-col md:flex-row border border-gray-100 dark:border-gray-800">
        
        {/* Left World Map Visual Panel */}
        <div className="hidden md:block w-1/2 h-[600px] relative overflow-hidden border-r border-gray-100 dark:border-gray-800">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-indigo-950">
            <WorldMap />
            <div className="absolute inset-0 flex flex-col items-center justify-center p-8 z-10 text-center">
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6, duration: 0.5 }}
                className="mb-6"
              >
                <div className="h-12 w-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-200 dark:shadow-none">
                  <Compass className="text-white h-6 w-6" />
                </div>
              </motion.div>

              <motion.h2
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7, duration: 0.5 }}
                className="text-3xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400"
              >
                RemitMind
              </motion.h2>

              <motion.p
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 0.5 }}
                className="text-sm text-gray-600 dark:text-gray-400 max-w-xs"
              >
                AI-powered remittance intelligence, rate forecasting & fraud defense for upay
              </motion.p>
            </div>
          </div>
        </div>

        {/* Right Form Panel */}
        <div className="w-full md:w-1/2 p-8 md:p-10 flex flex-col justify-center bg-white dark:bg-gray-900">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-2xl md:text-3xl font-bold mb-1 text-gray-800 dark:text-gray-100">
              Welcome back
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mb-8">
              Sign in to your account
            </p>

            {/* Google Sign In */}
            <div className="mb-6">
              <button
                type="button"
                className="w-full flex items-center justify-center gap-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:bg-gray-100 dark:hover:bg-gray-750 transition-all duration-300 text-gray-700 dark:text-gray-200 shadow-sm"
                onClick={() => console.log("Google sign-in")}
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                <span>Login with Google</span>
              </button>
            </div>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200 dark:border-gray-800" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white dark:bg-gray-900 text-gray-500">or</span>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email <span className="text-blue-500">*</span>
                </label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email address"
                  required
                  className="bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 placeholder:text-gray-400 text-gray-800 dark:text-gray-100 w-full focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Password <span className="text-blue-500">*</span>
                </label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    required
                    className="bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 placeholder:text-gray-400 text-gray-800 dark:text-gray-100 w-full pr-10 focus:border-blue-500 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <motion.div
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                onHoverStart={() => setIsHovered(true)}
                onHoverEnd={() => setIsHovered(false)}
                className="pt-2"
              >
                <Button
                  type="submit"
                  className={cn(
                    "w-full bg-gradient-to-r relative overflow-hidden from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white py-2 rounded-lg transition-all duration-300",
                    isHovered ? "shadow-lg shadow-blue-200 dark:shadow-blue-900/50" : ""
                  )}
                >
                  <span className="flex items-center justify-center">
                    Sign in
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </span>
                  {isHovered && (
                    <motion.span
                      initial={{ left: "-100%" }}
                      animate={{ left: "100%" }}
                      transition={{ duration: 1, ease: "easeInOut" }}
                      className="absolute top-0 bottom-0 left-0 w-20 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                      style={{ filter: "blur(8px)" }}
                    />
                  )}
                </Button>
              </motion.div>

              <div className="text-center mt-6">
                <a href="#" className="text-blue-600 hover:text-blue-700 text-sm transition-colors">
                  Forgot password?
                </a>
              </div>
            </form>
          </motion.div>
        </div>

      </div>
    </div>
  )
}
export { TravelConnectSignin1 }
