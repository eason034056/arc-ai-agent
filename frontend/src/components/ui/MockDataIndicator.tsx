// /**
//  * Mock Data Indicator
//  * Shows a badge when using mock data
//  */

// 'use client'

// import { USE_MOCK_DATA, SHOW_MOCK_INDICATOR } from '@/lib/api/apiConfig'

// export function MockDataIndicator() {
//   // Don't show if not using mock data or indicator is disabled
//   if (!USE_MOCK_DATA || !SHOW_MOCK_INDICATOR) {
//     return null
//   }

//   return (
//     <div className="fixed bottom-4 right-4 z-50">
//       <div className="bg-yellow-100 border-2 border-yellow-400 rounded-lg px-4 py-2 shadow-lg">
//         <div className="flex items-center gap-2">
//           <span className="text-2xl">🎭</span>
//           <div>
//             <p className="text-sm font-semibold text-yellow-800">
//               Using Mock Data
//             </p>
//             <p className="text-xs text-yellow-700">
//               Backend not connected
//             </p>
//           </div>
//         </div>
//       </div>
//     </div>
//   )
// }

// /**
//  * Mock Data Banner
//  * Shows a banner at the top when using mock data
//  */
// export function MockDataBanner() {
//   if (!USE_MOCK_DATA || !SHOW_MOCK_INDICATOR) {
//     return null
//   }

//   return (
//     <div className="bg-yellow-50 border-b border-yellow-200">
//       <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
//         <div className="flex items-center justify-between">
//           <div className="flex items-center gap-2">
//             <span className="text-lg">🎭</span>
//             <p className="text-sm text-yellow-800">
//               <span className="font-semibold">Development Mode:</span>{' '}
//               Using mock data. Connect backend to see real data.
//             </p>
//           </div>
//           <button
//             onClick={() => window.location.reload()}
//             className="text-xs text-yellow-700 hover:text-yellow-900 underline"
//           >
//             Refresh
//           </button>
//         </div>
//       </div>
//     </div>
//   )
// }
