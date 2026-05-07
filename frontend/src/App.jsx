import { BrowserRouter, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Upload, History, Pill, Brain, Shield, Zap, AlertTriangle, Database, TrendingUp, Camera, FileImage, FileText } from 'lucide-react';
import { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard.jsx';
import HistoryPage from './pages/History.jsx';
import Search from './pages/Search.jsx';

// Landing Page Component
function LandingPage() {
  const navigate = useNavigate();
  const [isTyping, setIsTyping] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsTyping(false), 3500);
    return () => clearTimeout(timer);
  }, []);

  const handleUploadClick = () => {
    console.log("Upload Prescription button clicked");
    try {
      navigate('/dashboard');
    } catch (error) {
      console.error("Navigation error:", error);
    }
  };

  const handleQuickUploadClick = () => {
    console.log("Quick Upload section clicked");
    try {
      navigate('/dashboard');
    } catch (error) {
      console.error("Navigation error:", error);
    }
  };

  const handleGetStartedClick = () => {
    console.log("Get Started button clicked");
    try {
      navigate('/dashboard');
    } catch (error) {
      console.error("Navigation error:", error);
    }
  };

  const handleWatchDemoClick = () => {
    console.log("Watch Demo button clicked");
    // Placeholder for demo video or modal logic
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="pt-20 pb-16 bg-gradient-to-br from-blue-50 via-white to-purple-50 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="space-y-4">
                <div className="inline-flex items-center px-4 py-2 bg-blue-100 rounded-full text-blue-700 text-sm font-medium">
                  <span className="mr-2">✨</span>
                  AI-Powered Healthcare Technology
                </div>
                <h1 className="text-5xl lg:text-6xl font-bold text-gray-900 leading-tight">
                  Read Prescriptions with{' '}
                  <span className={`bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent ${isTyping ? 'animate-pulse' : ''}`}>
                    AI Precision
                  </span>
                </h1>
                <p className="text-xl text-gray-600 max-w-2xl">
                  Transform handwritten prescriptions into digital data instantly. Our advanced AI technology ensures accuracy, saves time, and reduces medication errors for healthcare professionals.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <button 
                  onClick={handleUploadClick}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-4 rounded-xl font-semibold hover:shadow-xl transform hover:scale-105 transition-all duration-300 hover:shadow-blue-500/25 z-50 relative"
                >
                  <Upload className="w-5 h-5 mr-2 inline" />
                  Upload Prescription
                </button>
                <button 
                  onClick={handleWatchDemoClick}
                  className="border-2 border-gray-300 text-gray-700 px-8 py-4 rounded-xl font-semibold hover:border-blue-500 hover:text-blue-600 transition-all duration-300 z-50 relative"
                >
                  <span className="mr-2">▶</span>
                  Watch Demo
                </button>
              </div>

              <div className="flex items-center space-x-8 pt-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-900">99.9%</div>
                  <div className="text-gray-600">Accuracy Rate</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-900">10K+</div>
                  <div className="text-gray-600">Prescriptions Processed</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-900">500+</div>
                  <div className="text-gray-600">Healthcare Partners</div>
                </div>
              </div>
            </div>

            <div className="relative">
              <div className="relative">
                <div className="bg-white rounded-3xl shadow-2xl p-8 backdrop-blur-sm bg-white/90">
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xl font-semibold text-gray-800">Quick Upload</h3>
                      <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                        <span className="text-green-600">✓</span>
                      </div>
                    </div>
                    
                    <div 
                      onClick={handleQuickUploadClick}
                      className="border-2 border-dashed border-blue-300 rounded-xl p-8 text-center hover:border-blue-500 transition-colors duration-300 cursor-pointer group z-50 relative"
                    >
                      <Upload className="w-12 h-12 text-blue-500 mb-4 mx-auto group-hover:scale-110 transition-transform" />
                      <div className="text-gray-700 font-medium">Drop your prescription here</div>
                      <div className="text-gray-500 text-sm mt-2">or click to browse</div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <Camera className="w-4 h-4 text-blue-600" />
                        </div>
                        <span className="text-gray-700">Capture with camera</span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                          <FileImage className="w-4 h-4 text-purple-600" />
                        </div>
                        <span className="text-gray-700">Upload image file</span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                          <FileText className="w-4 h-4 text-green-600" />
                        </div>
                        <span className="text-gray-700">PDF documents</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="absolute -top-4 -right-4 w-20 h-20 bg-blue-200 rounded-2xl animate-bounce opacity-60"></div>
              <div className="absolute -bottom-4 -left-4 w-16 h-16 bg-purple-200 rounded-2xl animate-bounce opacity-60" style={{animationDelay: '1s'}}></div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Powerful Features</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Experience the future of prescription management with our cutting-edge AI technology
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<Brain className="w-8 h-8 text-blue-600" />}
              title="AI-Powered OCR"
              description="Advanced machine learning algorithms that can read even the most challenging handwriting with exceptional accuracy."
              bgColor="bg-blue-100"
            />
            <FeatureCard 
              icon={<Shield className="w-8 h-8 text-green-600" />}
              title="HIPAA Compliant"
              description="Enterprise-grade security ensures all patient data is protected and compliant with healthcare regulations."
              bgColor="bg-green-100"
            />
            <FeatureCard 
              icon={<Zap className="w-8 h-8 text-purple-600" />}
              title="Instant Processing"
              description="Get results in seconds, not minutes. Our optimized AI processes prescriptions faster than ever before."
              bgColor="bg-purple-100"
            />
            <FeatureCard 
              icon={<AlertTriangle className="w-8 h-8 text-red-600" />}
              title="Error Detection"
              description="Smart algorithms identify potential medication conflicts and dosage errors before they happen."
              bgColor="bg-red-100"
            />
            <FeatureCard 
              icon={<Database className="w-8 h-8 text-yellow-600" />}
              title="Drug Database"
              description="Access to comprehensive medication database with detailed information and interaction warnings."
              bgColor="bg-yellow-100"
            />
            <FeatureCard 
              icon={<TrendingUp className="w-8 h-8 text-indigo-600" />}
              title="Analytics Dashboard"
              description="Track processing metrics, accuracy rates, and gain insights into prescription patterns."
              bgColor="bg-indigo-100"
            />
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Three simple steps to transform your prescription workflow
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <StepCard number="1" title="Upload" description="Simply upload your prescription image or PDF. Our system accepts multiple formats and resolutions." />
            <StepCard number="2" title="Process" description="Our AI analyzes the prescription, extracting medication names, dosages, and instructions with high accuracy." />
            <StepCard number="3" title="Review" description="Review the digitized prescription data, make any necessary corrections, and export to your preferred format." />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-purple-700 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-0 left-0 w-full h-full bg-black opacity-10"></div>
          <div className="absolute top-10 left-10 w-32 h-32 bg-white rounded-full opacity-10 animate-pulse"></div>
          <div className="absolute bottom-10 right-10 w-40 h-40 bg-white rounded-full opacity-10 animate-pulse" style={{animationDelay: '1s'}}></div>
        </div>
        
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8 relative">
          <h2 className="text-4xl font-bold text-white mb-6">Ready to Transform Your Workflow?</h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join thousands of healthcare professionals who trust IntelliRx+ for accurate prescription processing.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button 
              onClick={handleGetStartedClick}
              className="bg-white text-blue-600 px-8 py-4 rounded-xl font-semibold hover:shadow-xl transform hover:scale-105 transition-all duration-300 z-50 relative"
            >
              Start Free Trial
            </button>
            <button className="border-2 border-white text-white px-8 py-4 rounded-xl font-semibold hover:bg-white hover:text-blue-600 transition-all duration-300 z-50 relative">
              Schedule Demo
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

// Feature Card Component
function FeatureCard({ icon, title, description, bgColor }) {
  return (
    <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 hover:shadow-xl hover:scale-105 transition-all duration-300">
      <div className={`w-16 h-16 ${bgColor} rounded-2xl flex items-center justify-center mb-6`}>
        {icon}
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-4">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

// Step Card Component
function StepCard({ number, title, description }) {
  return (
    <div className="text-center">
      <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
        <span className="text-2xl font-bold text-white">{number}</span>
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-4">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

// Navigation Component
function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  
  const navItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/dashboard', icon: Upload, label: 'Upload' },
    { path: '/history', icon: History, label: 'History' }
  ];

  // Don't show navbar on landing page
  if (location.pathname === '/') {
    return (
      <nav className="fixed w-full z-50 bg-white/80 backdrop-blur-md border-b border-gray-200/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Pill className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                IntelliRx+
              </span>
            </div>
            <div className="hidden md:flex space-x-8">
              <button 
                onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                className="text-gray-600 hover:text-blue-600 transition-colors duration-200"
              >
                Features
              </button>
              <button 
                onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}
                className="text-gray-600 hover:text-blue-600 transition-colors duration-200"
              >
                How it Works
              </button>
              <button className="text-gray-600 hover:text-blue-600 transition-colors duration-200">About</button>
              <button className="text-gray-600 hover:text-blue-600 transition-colors duration-200">Contact</button>
            </div>
            <div className="flex items-center space-x-4">
              <button className="text-gray-600 hover:text-blue-600 transition-colors duration-200">Sign In</button>
              <button 
                onClick={() => {
                  console.log("Navbar Get Started clicked");
                  try {
                    navigate('/dashboard');
                  } catch (error) {
                    console.error("Navigation error:", error);
                  }
                }}
                className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-2 rounded-lg hover:shadow-lg transform hover:scale-105 transition-all duration-200 z-50 relative"
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </nav>
    );
  }

  return (
    <nav className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2">
            <Pill className="w-8 h-8 text-blue-600" />
            <span className="text-xl font-bold text-gray-800">IntelliRx+</span>
          </Link>
          
          <div className="flex space-x-1">
            {navItems.map(({ path, icon: Icon, label }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  location.pathname === path
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:block">{label}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}

// Footer Component
function Footer() {
  const location = useLocation();
  
  // Only show footer on landing page
  if (location.pathname !== '/') {
    return null;
  }

  return (
    <footer className="bg-gray-900 text-white py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-4 gap-8">
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Pill className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold">IntelliRx+</span>
            </div>
            <p className="text-gray-400">
              Revolutionizing prescription management with AI-powered technology for healthcare professionals worldwide.
            </p>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-4">Product</h3>
            <div className="space-y-2">
              <button className="text-gray-400 hover:text-white transition-colors duration-200 block">Features</button>
              <button className="text-gray-400 hover:text-white transition-colors duration-200 block">Pricing</button>
              <button className="text-gray-400 hover:text-white transition-colors duration-200 block">API</button>
              <button className="text-gray-400 hover:text-white transition-colors duration-200 block">Documentation</button>
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-4">Company</h3>
            <div className="space-y-2">
              <button className="text-gray-400 hover:text-white transition-colors duration-200 block">About</button>
              <button className="text-gray-400 hover:text-white transition-colors duration-200 block">Blog</button>
              <button className="text-gray-400 hover:text-white transition-colors duration-200 block">Careers</button>
              <button className="text-gray-400 hover:text-white transition-colors duration-200 block">Contact</button>
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-4">Support</h3>
            <div className="space-y-2">
              <button className="text-gray-400 hover:text-white transition-colors duration-200 block">Help Center</button>
              <button className="text-gray-400 hover:text-white transition-colors duration-200 block">Privacy Policy</button>
              <button className="text-gray-400 hover:text-white transition-colors duration-200 block">Terms of Service</button>
              <button className="text-gray-400 hover:text-white transition-colors duration-200 block">Security</button>
            </div>
          </div>
        </div>
        
        <div className="border-t border-gray-800 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-gray-400">© 2025 IntelliRx+. All rights reserved.</p>
          <div className="flex space-x-6 mt-4 md:mt-0">
            <button className="text-gray-400 hover:text-white transition-colors duration-200">
              Twitter
            </button>
            <button className="text-gray-400 hover:text-white transition-colors duration-200">
              LinkedIn
            </button>
            <button className="text-gray-400 hover:text-white transition-colors duration-200">
              GitHub
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}

// Main App Component
function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/search" element={<Search />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
        <Footer />
      </div>
    </BrowserRouter>
  );
}

export default App;