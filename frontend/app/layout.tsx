import type { Metadata } from "next";                                                                                                                                          
    import { Geist, Geist_Mono } from "next/font/google";                                                                                                                          
    import "./globals.css";                                                                                                                                                        
    // 1. Import your QueryProvider                                                                                                                                                
    import { QueryProvider } from "@/components/providers/query-provider";                                                                                                         
                                                                                                                                                                                   
    const geistSans = Geist({                                                                                                                                                      
      variable: "--font-geist-sans",                                                                                                                                               
      subsets: ["latin"],                                                                                                                                                          
    });                                                                                                                                                                            
                                                                                                                                                                                   
    const geistMono = Geist_Mono({                                                                                                                                                 
      variable: "--font-geist-mono",                                                                                                                                               
      subsets: ["latin"],                                                                                                                                                          
    });                                                                                                                                                                            
                                                                                                                                                                                   
    export const metadata: Metadata = {
      title: "Society Management System",
      description: "Enterprise Multi-Tenant Society Platform",
    };
  
    export default function RootLayout({
      children,
    }: {
      children: React.ReactNode;
    }) {
      return (
        <html
          lang="en"
          className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
        >
          <body className="min-h-full flex flex-col">
            {/* 2. Wrap children here */}
            <QueryProvider>
              {children}
            </QueryProvider>
          </body>
        </html>
      );
    }
  