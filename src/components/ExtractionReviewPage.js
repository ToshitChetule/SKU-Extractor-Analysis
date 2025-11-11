// import React, { useMemo, useState } from "react";
// import { useNavigate } from "react-router-dom";
// import { useLocation } from "react-router-dom";
// import * as XLSX from "xlsx";
// import { jsPDF } from "jspdf";
// import "jspdf-autotable";
// import Swal from "sweetalert2";



// export default function ExtractionReviewPage() {
//   const navigate = useNavigate();
//   const location = useLocation();
//   const { uploadedFilename, sku_matrix = [], aggregated_matrix = {} } =
//     location.state || {};

//   const [viewMode, setViewMode] = useState("config"); // "config" | "aggregated"
//   const [attributeSearch, setAttributeSearch] = useState("");
//   const [valueSearch, setValueSearch] = useState("");
//   const [prompt, setPrompt] = useState("");
//   const [selectedRows, setSelectedRows] = useState([]);
//   const [exportMenuOpen, setExportMenuOpen] = useState(false);
//   const [loading, setLoading] = useState(false);

//   const storedUser = JSON.parse(localStorage.getItem("user"));
//   const username = storedUser?.username || "User";

//   // ✅ Extract unique attributes from all SKUs
//   const allAttributes = useMemo(() => {
//     const attrs = new Set();
//     sku_matrix.forEach((s) => s.attributes.forEach(([a]) => attrs.add(a)));
//     return Array.from(attrs);
//   }, [sku_matrix]);

//   // ✅ Build configuration matrix
//   const matrixRows = useMemo(() => {
//     return sku_matrix.map((skuObj) => {
//       const row = { SKU: skuObj.sku };
//       allAttributes.forEach((a) => {
//         const found = skuObj.attributes.find(([attr]) => attr === a);
//         row[a] = found ? found[1] : "";
//       });
//       return row;
//     });
//   }, [sku_matrix, allAttributes]);

//   // ✅ Filter logic
//   const filteredRows = useMemo(() => {
//     if (viewMode === "config") {
//       return matrixRows.filter((row) => {
//         const attrMatch = Object.keys(row)
//           .join(" ")
//           .toLowerCase()
//           .includes(attributeSearch.toLowerCase());
//         const valMatch = Object.values(row)
//           .join(" ")
//           .toLowerCase()
//           .includes(valueSearch.toLowerCase());
//         return attrMatch && valMatch;
//       });
//     } else {
//       // Aggregated Attributes View Filtering
//       const columns = aggregated_matrix.columns || [];
//       const rows = aggregated_matrix.rows || [];

//       return rows.filter((row) => {
//         const headerText = columns.join(" ").toLowerCase();
//         const rowText = row.join(" ").toLowerCase();
//         const attrMatch =
//           !attributeSearch ||
//           headerText.includes(attributeSearch.toLowerCase());
//         const valMatch =
//           !valueSearch || rowText.includes(valueSearch.toLowerCase());
//         return attrMatch && valMatch;
//       });
//     }
//   }, [matrixRows, aggregated_matrix, attributeSearch, valueSearch, viewMode]);

//   // ✅ Select all toggle
//   const toggleSelectAll = (checked) => {
//     setSelectedRows(checked ? filteredRows.map((r) => r.SKU) : []);
//   };

//   // ✅ Export
//   const handleExport = (format) => {
//     let data, filename, columns, rows;

//     if (viewMode === "config") {
//       data = matrixRows;
//       filename = `${uploadedFilename}_Configuration_Matrix`;
//     } else {
//       columns = aggregated_matrix.columns || [];
//       rows = aggregated_matrix.rows || [];
//       data = rows.map((r) =>
//         Object.fromEntries(columns.map((c, i) => [c, r[i]]))
//       );
//       filename = `${uploadedFilename}_Aggregated_Attributes`;
//     }

//     if (format === "xlsx") {
//       const ws = XLSX.utils.json_to_sheet(data);
//       const wb = XLSX.utils.book_new();
//       XLSX.utils.book_append_sheet(
//         wb,
//         ws,
//         viewMode === "config" ? "Configuration" : "Aggregated"
//       );
//       XLSX.writeFile(wb, `${filename}.xlsx`);
//     } else if (format === "pdf") {
//       const doc = new jsPDF();
//       doc.text(filename, 14, 16);
//       if (viewMode === "config") {
//         doc.autoTable({
//           head: [Object.keys(matrixRows[0] || {})],
//           body: filteredRows.map((r) => Object.values(r)),
//           startY: 20,
//           styles: { fontSize: 8 },
//         });
//       } else {
//         doc.autoTable({
//           head: [columns],
//           body: rows,
//           startY: 20,
//           styles: { fontSize: 8 },
//         });
//       }
//       doc.save(`${filename}.pdf`);
//     }

//     Swal.fire({
//       icon: "success",
//       title: "Exported Successfully!",
//       timer: 1500,
//       showConfirmButton: false,
//     });
//     setExportMenuOpen(false);
//   };

//   // ✅ Refine placeholder
//   const handleRefineAttributes = () => {
//     if (!selectedRows.length) {
//       Swal.fire("Select at least one SKU row.", "", "info");
//       return;
//     }
//     if (!prompt.trim()) {
//       Swal.fire("Please enter a refinement prompt.", "", "warning");
//       return;
//     }
//     Swal.fire("✨ Coming Soon!", "AI refinement will be added later.", "info");
//   };

//   return (
//     <div
//       style={{
//         background: "linear-gradient(135deg, #f8fafc, #e0e7ff)",
//         minHeight: "100vh",
//         fontFamily: "'Inter', sans-serif",
//         color: "#1e293b",
//       }}
//     >
//       {/* HEADER */}
//       <header
//         style={{
//           display: "flex",
//           alignItems: "center",
//           padding: "24px",
//           background: "rgba(255,255,255,0.6)",
//           backdropFilter: "blur(10px)",
//           boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
//         }}
//       >
//         <img
//           src="https://img.icons8.com/fluency/96/000000/bot.png"
//           alt="bot"
//           style={{ width: 48, height: 48, marginRight: 16 }}
//         />
//         <h2 style={{ margin: 0, fontWeight: 700 }}>
//           {viewMode === "config"
//             ? "Configuration Matrix (Per SKU)"
//             : "Aggregated Attributes"}
//         </h2>
//         <span
//           style={{
//             marginLeft: "auto",
//             background: "rgba(255,255,255,0.5)",
//             padding: "8px 16px",
//             borderRadius: 12,
//             fontWeight: 600,
//           }}
//         >
//           Hi {username} 👋
//         </span>
//       </header>

//       <main
//         style={{
//           padding: 30,
//           display: "flex",
//           justifyContent: "center",
//         }}
//       >
//         <div
//           style={{
//             width: "95%",
//             background: "rgba(255,255,255,0.9)",
//             borderRadius: 20,
//             boxShadow: "0 10px 40px rgba(0,0,0,0.1)",
//             padding: 24,
//             backdropFilter: "blur(15px)",
//           }}
//         >
//           {/* Controls */}
//           <div
//             style={{
//               display: "flex",
//               justifyContent: "space-between",
//               alignItems: "center",
//               gap: 10,
//               marginBottom: 20,
//             }}
//           >
//             <div style={{ display: "flex", gap: 10, flex: 1 }}>
//               <input
//                 placeholder="Search by Attribute..."
//                 value={attributeSearch}
//                 onChange={(e) => setAttributeSearch(e.target.value)}
//                 style={searchInputStyle}
//               />
//               <input
//                 placeholder="Search by Value..."
//                 value={valueSearch}
//                 onChange={(e) => setValueSearch(e.target.value)}
//                 style={searchInputStyle}
//               />
//             </div>

//             <div style={{ position: "relative" }}>
//               <button
//                 style={buttonStyle}
//                 onClick={() => setExportMenuOpen(!exportMenuOpen)}
//               >
//                 Export ▼
//               </button>
//               {exportMenuOpen && (
//                 <div style={exportMenuStyle}>
//                   {["xlsx", "pdf"].map((fmt) => (
//                     <div
//                       key={fmt}
//                       onClick={() => handleExport(fmt)}
//                       style={exportMenuItemStyle}
//                     >
//                       Export as {fmt.toUpperCase()}
//                     </div>
//                   ))}
//                 </div>
//               )}
//             </div>

//             <div style={{ display: "flex", gap: 10 }}>
//               <button
//                 style={{
//                   ...buttonStyle,
//                   background: "linear-gradient(135deg, #16a34a, #22c55e)",
//                 }}
//                 onClick={() =>
//                   setViewMode(viewMode === "config" ? "aggregated" : "config")
//                 }
//               >
//                 {viewMode === "config"
//                   ? "View Aggregated Attributes"
//                   : "← Back to Configuration Matrix"}
//               </button>

//               {viewMode === "aggregated" && (
//                 <button
//                   style={{
//                     ...buttonStyle,
//                     background: "linear-gradient(135deg, #3b82f6, #2563eb)",
//                   }}
//                   onClick={() => navigate("/variant")}
//                 >
//                   Variant Attribute Analysis
//                 </button>
//               )}
//             </div>

//           </div>

//           {/* Prompt */}
//           <div style={{ display: "flex", gap: 10, marginBottom: 24 }}>
//             <textarea
//               placeholder="Write a prompt to refine selected attributes..."
//               value={prompt}
//               onChange={(e) => setPrompt(e.target.value)}
//               style={textareaStyle}
//             />
//             <button onClick={handleRefineAttributes} style={buttonStyle}>
//               {loading ? "Refining..." : "Refine Attributes"}
//             </button>
//           </div>

//           {/* Table */}
//           <div style={scrollContainerStyle}>
//             <table style={tableStyle}>
//               <thead style={theadStyle}>
//                 {viewMode === "config" ? (
//                   <tr>
//                     <th style={stickyCheckCol}>
//                       <input
//                         type="checkbox"
//                         onChange={(e) => toggleSelectAll(e.target.checked)}
//                         checked={
//                           selectedRows.length === filteredRows.length &&
//                           filteredRows.length > 0
//                         }
//                       />
//                     </th>
//                     {["SKU Description", ...allAttributes].map((attr, idx) => (
//                       <th
//                         key={idx}
//                         style={{
//                           ...thStyle,
//                           ...(attr === "SKU Description" ? stickySKUCol : {}),
//                         }}
//                       >
//                         {attr}
//                       </th>
//                     ))}
//                   </tr>
//                 ) : (
//                   <tr>
//                     {(aggregated_matrix.columns || []).map((col, idx) => (
//                       <th key={idx} style={thStyle}>
//                         {col}
//                       </th>
//                     ))}
//                   </tr>
//                 )}
//               </thead>

//               <tbody>
//                 {viewMode === "config"
//                   ? filteredRows.map((row, idx) => (
//                     <tr
//                       key={idx}
//                       style={{
//                         ...tbodyRowStyle,
//                         background:
//                           idx % 2 === 0
//                             ? "rgba(255,255,255,0.9)"
//                             : "rgba(249,250,251,0.9)",
//                       }}
//                     >
//                       <td style={stickyCheckCol}>
//                         <input
//                           type="checkbox"
//                           checked={selectedRows.includes(row.SKU)}
//                           onChange={(e) => {
//                             const updated = e.target.checked
//                               ? [...selectedRows, row.SKU]
//                               : selectedRows.filter((r) => r !== row.SKU);
//                             setSelectedRows(updated);
//                           }}
//                         />
//                       </td>
//                       {["SKU", ...allAttributes].map((a, j) => (
//                         <td
//                           key={j}
//                           style={{
//                             ...tdStyle,
//                             ...(a === "SKU" ? stickySKUCol : {}),
//                           }}
//                         >
//                           {row[a]}
//                         </td>
//                       ))}
//                     </tr>
//                   ))
//                   : (aggregated_matrix.rows || []).map((row, i) => (
//                     <tr key={i} style={tbodyRowStyle}>
//                       {row.map((cell, j) => (
//                         <td key={j} style={tdStyle}>
//                           {cell}
//                         </td>
//                       ))}
//                     </tr>
//                   ))}
//               </tbody>
//             </table>
//           </div>
//         </div>
//       </main>
//     </div>
//   );
// }

// /* ✨ Styles */
// const searchInputStyle = {
//   flex: 1,
//   padding: "12px 14px",
//   borderRadius: "10px",
//   border: "1px solid #cbd5e1",
//   outline: "none",
//   background: "rgba(255,255,255,0.8)",
//   fontSize: "15px",
//   transition: "0.2s",
// };

// const buttonStyle = {
//   padding: "10px 20px",
//   borderRadius: 8,
//   border: "none",
//   background: "linear-gradient(135deg,#6366f1,#3b82f6)",
//   color: "white",
//   fontWeight: 600,
//   cursor: "pointer",
//   boxShadow: "0 4px 10px rgba(59,130,246,0.3)",
//   transition: "all 0.25s ease",
// };

// const tableStyle = {
//   width: "100%",
//   borderCollapse: "collapse",
//   fontSize: "14px",
// };

// const theadStyle = {
//   background: "linear-gradient(135deg,#eef2ff,#dbeafe)",
//   position: "sticky",
//   top: 0,
//   zIndex: 10,
// };

// const thStyle = {
//   padding: "12px",
//   borderBottom: "2px solid #cbd5e1",
//   borderRight: "1px solid #e5e7eb", // ✅ Light vertical line
//   fontWeight: 700,
//   color: "#1e293b",
//   textAlign: "left",
//   whiteSpace: "nowrap",
// };

// const tdStyle = {
//   padding: "10px",
//   borderBottom: "1px solid #e2e8f0",
//   borderRight: "1px solid #e5e7eb", // ✅ Light vertical separator
//   color: "#334155",
//   background: "rgba(255,255,255,0.95)",
//   whiteSpace: "nowrap",
// };

// const stickyCheckCol = {
//   position: "sticky",
//   left: 0,
//   background: "rgba(240,242,255,0.98)",
//   boxShadow: "2px 0 6px rgba(0,0,0,0.05)",
//   zIndex: 8,
//   textAlign: "center",
//   width: "60px",
//   borderRight: "1px solid #e5e7eb",
// };

// const stickySKUCol = {
//   position: "sticky",
//   left: "22.4px",
//   background: "rgba(240,242,255,0.98)",
//   boxShadow: "2px 0 6px rgba(0,0,0,0.05)",
//   zIndex: 7,
//   fontWeight: 600,
//   minWidth: "220px",
//   borderRight: "1px solid #e5e7eb",
// };

// const tbodyRowStyle = {
//   transition: "background 0.2s ease",
// };

// const textareaStyle = {
//   flex: 1,
//   minHeight: 80,
//   padding: "12px 14px",
//   borderRadius: 10,
//   border: "1px solid #cbd5e1",
//   background: "rgba(255,255,255,0.9)",
//   resize: "vertical",
// };

// const scrollContainerStyle = {
//   maxHeight: "85vh", // ⬆ taller view
//   overflow: "auto",
//   borderRadius: 12,
//   boxShadow: "inset 0 0 10px rgba(0,0,0,0.05)",
// };

// const exportMenuStyle = {
//   position: "absolute",
//   right: 0,
//   top: "110%",
//   background: "white",
//   boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
//   borderRadius: 8,
//   overflow: "hidden",
//   zIndex: 100,
// };

// const exportMenuItemStyle = {
//   padding: "10px 16px",
//   cursor: "pointer",
//   borderBottom: "1px solid #eee",
//   transition: "background 0.2s",
// };


import React, { useMemo, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import * as XLSX from "xlsx";
import { jsPDF } from "jspdf";
import "jspdf-autotable";
import Swal from "sweetalert2";


export default function ExtractionReviewPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { uploadedFilename, sku_matrix = [], aggregated_matrix = {} } =
    location.state || {};

  const [viewMode, setViewMode] = useState("config"); // "config" | "aggregated"
  const [attributeSearch, setAttributeSearch] = useState("");
  const [valueSearch, setValueSearch] = useState("");
  const [prompt, setPrompt] = useState("");
  const [selectedRows, setSelectedRows] = useState([]);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [localAggregated, setLocalAggregated] = useState(aggregated_matrix);

  const storedUser = JSON.parse(localStorage.getItem("user"));
  const username = storedUser?.username || "User";

  // ✅ Extract unique attributes from all SKUs
  const allAttributes = useMemo(() => {
    const attrs = new Set();
    sku_matrix.forEach((s) => s.attributes.forEach(([a]) => attrs.add(a)));
    return Array.from(attrs);
  }, [sku_matrix]);

  // ✅ Build configuration matrix
  const matrixRows = useMemo(() => {
    return sku_matrix.map((skuObj) => {
      const row = { SKU: skuObj.sku };
      allAttributes.forEach((a) => {
        const found = skuObj.attributes.find(([attr]) => attr === a);
        row[a] = found ? found[1] : "";
      });
      return row;
    });
  }, [sku_matrix, allAttributes]);

  // ✅ Filter logic
  const filteredRows = useMemo(() => {
    if (viewMode === "config") {
      return matrixRows.filter((row) => {
        const attrMatch = Object.keys(row)
          .join(" ")
          .toLowerCase()
          .includes(attributeSearch.toLowerCase());
        const valMatch = Object.values(row)
          .join(" ")
          .toLowerCase()
          .includes(valueSearch.toLowerCase());
        return attrMatch && valMatch;
      });
    } else {
      const columns = localAggregated.columns || [];
      const rows = localAggregated.rows || [];

      return rows.filter((row) => {
        const headerText = columns.join(" ").toLowerCase();
        const rowText = row.join(" ").toLowerCase();
        const attrMatch =
          !attributeSearch ||
          headerText.includes(attributeSearch.toLowerCase());
        const valMatch =
          !valueSearch || rowText.includes(valueSearch.toLowerCase());
        return attrMatch && valMatch;
      });
    }
  }, [matrixRows, localAggregated, attributeSearch, valueSearch, viewMode]);

  // ✅ Select all toggle
  const toggleSelectAll = (checked) => {
    setSelectedRows(checked ? filteredRows.map((r) => r.SKU) : []);
  };

  // ✅ Export logic
  // const handleExport = (format) => {
  //   let data, filename, columns, rows;

  //   if (viewMode === "config") {
  //     data = matrixRows;
  //     filename = `${uploadedFilename}_Configuration_Matrix`;
  //   } else {
  //     columns = localAggregated.columns || [];
  //     rows = localAggregated.rows || [];
  //     data = rows.map((r) =>
  //       Object.fromEntries(columns.map((c, i) => [c, r[i]]))
  //     );
  //     filename = `${uploadedFilename}_Aggregated_Attributes`;
  //   }

  //   if (format === "xlsx") {
  //     const ws = XLSX.utils.json_to_sheet(data);
  //     const wb = XLSX.utils.book_new();
  //     XLSX.utils.book_append_sheet(
  //       wb,
  //       ws,
  //       viewMode === "config" ? "Configuration" : "Aggregated"
  //     );
  //     XLSX.writeFile(wb, `${filename}.xlsx`);
  //   } else if (format === "pdf") {
  //     const doc = new jsPDF();
  //     doc.text(filename, 14, 16);
  //     if (viewMode === "config") {
  //       doc.autoTable({
  //         head: [Object.keys(matrixRows[0] || {})],
  //         body: filteredRows.map((r) => Object.values(r)),
  //         startY: 20,
  //         styles: { fontSize: 8 },
  //       });
  //     } else {
  //       doc.autoTable({
  //         head: [columns],
  //         body: rows,
  //         startY: 20,
  //         styles: { fontSize: 8 },
  //       });
  //     }
  //     doc.save(`${filename}.pdf`);
  //   }

  //   Swal.fire({
  //     icon: "success",
  //     title: "Exported Successfully!",
  //     timer: 1500,
  //     showConfirmButton: false,
  //   });
  //   setExportMenuOpen(false);
  // };

  // ✅ Export logic (Fixed & Enhanced)
const handleExport = (format) => {
  try {
    let data, filename, columns, rows;

    // 🧩 Case 1: Configuration Matrix View
    if (viewMode === "config") {
      data = matrixRows;
      filename = uploadedFilename
        ? `${uploadedFilename.replace(/\.[^/.]+$/, "")}_Configuration_Matrix`
        : "Configuration_Matrix";
    }
    // 🧩 Case 2: Aggregated Attributes View
    else {
      columns = localAggregated.columns || [];
      rows = localAggregated.rows || [];

      if (!columns.length || !rows.length) {
        Swal.fire("No data available to export.", "", "info");
        return;
      }

      data = rows.map((r) =>
        Object.fromEntries(columns.map((c, i) => [c, r[i]]))
      );
      filename = uploadedFilename
        ? `${uploadedFilename.replace(/\.[^/.]+$/, "")}_Aggregated_Attributes`
        : "Aggregated_Attributes";
    }

    // ✅ Excel Export
    if (format === "xlsx") {
      const ws = XLSX.utils.json_to_sheet(data);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(
        wb,
        ws,
        viewMode === "config" ? "Configuration" : "Aggregated"
      );
      XLSX.writeFile(wb, `${filename}.xlsx`);

      Swal.fire({
        icon: "success",
        title: "Excel Exported Successfully!",
        timer: 1500,
        showConfirmButton: false,
      });
    }

    // ✅ PDF Export
    else if (format === "pdf") {
      const doc = new jsPDF({
        orientation: "landscape",
        unit: "pt",
        format: "a4",
      });

      doc.setFontSize(14);
      doc.text(filename, 40, 40);

      // AutoTable content
      if (viewMode === "config") {
        const headers = Object.keys(matrixRows[0] || {});
        const body = filteredRows.map((r) => Object.values(r));

        doc.autoTable({
          head: [headers],
          body,
          startY: 60,
          styles: { fontSize: 8, overflow: "linebreak" },
          headStyles: { fillColor: [99, 102, 241] },
        });
      } else {
        doc.autoTable({
          head: [columns],
          body: rows,
          startY: 60,
          styles: { fontSize: 8, overflow: "linebreak" },
          headStyles: { fillColor: [59, 130, 246] },
        });
      }

      doc.save(`${filename}.pdf`);

      Swal.fire({
        icon: "success",
        title: "PDF Exported Successfully!",
        timer: 1500,
        showConfirmButton: false,
      });
    }

    setExportMenuOpen(false);
  } catch (err) {
    console.error("Export Error:", err);
    Swal.fire("Error", err.message, "error");
  }
};




  // ✅ Graph-based Refinement with Live UI Update
  const handleRefineAttributes = async () => {
    if (!prompt.trim()) {
      Swal.fire("Please enter a refinement prompt.", "", "warning");
      return;
    }

    if (viewMode !== "aggregated") {
      Swal.fire(
        "Switch to Aggregated View",
        "Refinement is available only in Aggregated Attributes view.",
        "info"
      );
      return;
    }

    const columns = localAggregated.columns || [];
    const rows = localAggregated.rows || [];
    const filteredAttributes = rows.filter((r) =>
      r[0].toLowerCase().includes(attributeSearch.toLowerCase())
    );

    if (!filteredAttributes.length) {
      Swal.fire("Please search and select an Attribute to refine.", "", "info");
      return;
    }

    const attribute = filteredAttributes[0][0];
    setLoading(true);

    try {
      const response = await fetch("http://localhost:5000/refine_graph", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          attribute: attribute,
          prompt: prompt,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        Swal.fire("Refinement Failed", result.error || "Unknown error", "error");
      } else {
        const updated = result.updated_context || {};
        const newAttr = updated.attribute;
        const newValues = updated.values || [];

        // 🧠 Update aggregated matrix in-place
        const newAggregated = { ...localAggregated };
        const rowIndex = (newAggregated.rows || []).findIndex(
          (r) => r[0] === attribute
        );

        if (rowIndex !== -1) {
          const newRow = [newAttr, ...newValues];
          while (newRow.length < newAggregated.columns.length) {
            newRow.push("");
          }
          newAggregated.rows[rowIndex] = newRow;
        } else {
          const newRow = [newAttr, ...newValues];
          while (newRow.length < newAggregated.columns.length) {
            newRow.push("");
          }
          newAggregated.rows.push(newRow);
        }

        setLocalAggregated(newAggregated); // Trigger re-render

        Swal.fire({
          icon: "success",
          title: "Refined Successfully!",
          html: `
            <div style="text-align:left">
              <p><b>Attribute:</b> ${newAttr}</p>
              <p><b>Values:</b> ${newValues.join(", ")}</p>
              <p><b>Related Attributes:</b> ${(updated.related_attributes || []).join(", ")}</p>
            </div>
          `,
          confirmButtonText: "OK",
        });
      }
    } catch (err) {
      Swal.fire("Error", err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  // ✅ UI Rendering
  return (
    <div
      style={{
        background: "linear-gradient(135deg, #f8fafc, #e0e7ff)",
        minHeight: "100vh",
        fontFamily: "'Inter', sans-serif",
        color: "#1e293b",
      }}
    >
      {/* HEADER */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          padding: "24px",
          background: "rgba(255,255,255,0.6)",
          backdropFilter: "blur(10px)",
          boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
        }}
      >
        <img
          src="https://img.icons8.com/fluency/96/000000/bot.png"
          alt="bot"
          style={{ width: 48, height: 48, marginRight: 16 }}
        />
        <h2 style={{ margin: 0, fontWeight: 700 }}>
          {viewMode === "config"
            ? "Configuration Matrix (Per SKU)"
            : "Aggregated Attributes"}
        </h2>
        <span
          style={{
            marginLeft: "auto",
            background: "rgba(255,255,255,0.5)",
            padding: "8px 16px",
            borderRadius: 12,
            fontWeight: 600,
          }}
        >
          Hi {username} 👋
        </span>
      </header>

      <main
        style={{
          padding: 30,
          display: "flex",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            width: "95%",
            background: "rgba(255,255,255,0.9)",
            borderRadius: 20,
            boxShadow: "0 10px 40px rgba(0,0,0,0.1)",
            padding: 24,
            backdropFilter: "blur(15px)",
          }}
        >
          {/* Controls */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 10,
              marginBottom: 20,
            }}
          >
            <div style={{ display: "flex", gap: 10, flex: 1 }}>
              <input
                placeholder="Search by Attribute..."
                value={attributeSearch}
                onChange={(e) => setAttributeSearch(e.target.value)}
                style={searchInputStyle}
              />
              <input
                placeholder="Search by Value..."
                value={valueSearch}
                onChange={(e) => setValueSearch(e.target.value)}
                style={searchInputStyle}
              />
            </div>

            <div style={{ position: "relative" }}>
              <button
                style={buttonStyle}
                onClick={() => setExportMenuOpen(!exportMenuOpen)}
              >
                Export ▼
              </button>
              {exportMenuOpen && (
                <div style={exportMenuStyle}>
                  {["xlsx", "pdf"].map((fmt) => (
                    <div
                      key={fmt}
                      onClick={() => handleExport(fmt)}
                      style={exportMenuItemStyle}
                    >
                      Export as {fmt.toUpperCase()}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div style={{ display: "flex", gap: 10 }}>
              <button
                style={{
                  ...buttonStyle,
                  background: "linear-gradient(135deg, #16a34a, #22c55e)",
                }}
                onClick={() =>
                  setViewMode(viewMode === "config" ? "aggregated" : "config")
                }
              >
                {viewMode === "config"
                  ? "View Aggregated Attributes"
                  : "← Back to Configuration Matrix"}
              </button>

              {/* {viewMode === "aggregated" && (

              <button
                style={{
                  ...buttonStyle,
                  background: "linear-gradient(135deg, #f59e0b, #fbbf24)",
                }}
                onClick={handleCompareAttributes}
              >
                Compare UI vs Graph
              </button>
            )} */}


              {viewMode === "aggregated" && (
                <button
                  style={{
                    ...buttonStyle,
                    background: "linear-gradient(135deg, #3b82f6, #2563eb)",
                  }}
                  onClick={() => navigate("/variant")}
                >
                  Variant Attribute Analysis
                </button>
              )}
            </div>
          </div>

          {/* Prompt */}
          <div style={{ display: "flex", gap: 10, marginBottom: 24 }}>
            <textarea
              placeholder="Write a prompt to refine selected attributes..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              style={textareaStyle}
            />
            <button onClick={handleRefineAttributes} style={buttonStyle}>
              {loading ? "Refining..." : "Refine Attributes"}
            </button>
          </div>

          {/* Table */}
          <div style={scrollContainerStyle}>
            <table style={tableStyle}>
              <thead style={theadStyle}>
                {viewMode === "config" ? (
                  <tr>
                    <th style={stickyCheckCol}>
                      <input
                        type="checkbox"
                        onChange={(e) => toggleSelectAll(e.target.checked)}
                        checked={
                          selectedRows.length === filteredRows.length &&
                          filteredRows.length > 0
                        }
                      />
                    </th>
                    {["SKU Description", ...allAttributes].map((attr, idx) => (
                      <th
                        key={idx}
                        style={{
                          ...thStyle,
                          ...(attr === "SKU Description" ? stickySKUCol : {}),
                        }}
                      >
                        {attr}
                      </th>
                    ))}
                  </tr>
                ) : (
                  <tr>
                    {(localAggregated.columns || []).map((col, idx) => (
                      <th key={idx} style={thStyle}>
                        {col}
                      </th>
                    ))}
                  </tr>
                )}
              </thead>

              <tbody>
                {viewMode === "config"
                  ? filteredRows.map((row, idx) => (
                      <tr
                        key={idx}
                        style={{
                          ...tbodyRowStyle,
                          background:
                            idx % 2 === 0
                              ? "rgba(255,255,255,0.9)"
                              : "rgba(249,250,251,0.9)",
                        }}
                      >
                        <td style={stickyCheckCol}>
                          <input
                            type="checkbox"
                            checked={selectedRows.includes(row.SKU)}
                            onChange={(e) => {
                              const updated = e.target.checked
                                ? [...selectedRows, row.SKU]
                                : selectedRows.filter((r) => r !== row.SKU);
                              setSelectedRows(updated);
                            }}
                          />
                        </td>
                        {["SKU", ...allAttributes].map((a, j) => (
                          <td
                            key={j}
                            style={{
                              ...tdStyle,
                              ...(a === "SKU" ? stickySKUCol : {}),
                            }}
                          >
                            {row[a]}
                          </td>
                        ))}
                      </tr>
                    ))
                  : (localAggregated.rows || []).map((row, i) => (
                      <tr key={i} style={tbodyRowStyle}>
                        {row.map((cell, j) => (
                          <td key={j} style={tdStyle}>
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

/* ✨ Styles (unchanged) */
const searchInputStyle = {
  flex: 1,
  padding: "12px 14px",
  borderRadius: "10px",
  border: "1px solid #cbd5e1",
  outline: "none",
  background: "rgba(255,255,255,0.8)",
  fontSize: "15px",
  transition: "0.2s",
};

const buttonStyle = {
  padding: "10px 20px",
  borderRadius: 8,
  border: "none",
  background: "linear-gradient(135deg,#6366f1,#3b82f6)",
  color: "white",
  fontWeight: 600,
  cursor: "pointer",
  boxShadow: "0 4px 10px rgba(59,130,246,0.3)",
  transition: "all 0.25s ease",
};

const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: "14px" };
const theadStyle = { background: "linear-gradient(135deg,#eef2ff,#dbeafe)", position: "sticky", top: 0, zIndex: 10 };
const thStyle = {
  padding: "12px",
  borderBottom: "2px solid #cbd5e1",
  borderRight: "1px solid #e5e7eb",
  fontWeight: 700,
  color: "#1e293b",
  textAlign: "left",
  whiteSpace: "nowrap",
};
const tdStyle = {
  padding: "10px",
  borderBottom: "1px solid #e2e8f0",
  borderRight: "1px solid #e5e7eb",
  color: "#334155",
  background: "rgba(255,255,255,0.95)",
  whiteSpace: "nowrap",
};
const stickyCheckCol = {
  position: "sticky",
  left: 0,
  background: "rgba(240,242,255,0.98)",
  boxShadow: "2px 0 6px rgba(0,0,0,0.05)",
  zIndex: 8,
  textAlign: "center",
  width: "60px",
  borderRight: "1px solid #e5e7eb",
};
const stickySKUCol = {
  position: "sticky",
  left: "22.4px",
  background: "rgba(240,242,255,0.98)",
  boxShadow: "2px 0 6px rgba(0,0,0,0.05)",
  zIndex: 7,
  fontWeight: 600,
  minWidth: "220px",
  borderRight: "1px solid #e5e7eb",
};
const tbodyRowStyle = { transition: "background 0.2s ease" };
const textareaStyle = {
  flex: 1,
  minHeight: 80,
  padding: "12px 14px",
  borderRadius: 10,
  border: "1px solid #cbd5e1",
  background: "rgba(255,255,255,0.9)",
  resize: "vertical",
};
const scrollContainerStyle = {
  maxHeight: "85vh",
  overflow: "auto",
  borderRadius: 12,
  boxShadow: "inset 0 0 10px rgba(0,0,0,0.05)",
};
const exportMenuStyle = {
  position: "absolute",
  right: 0,
  top: "110%",
  background: "white",
  boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
  borderRadius: 8,
  overflow: "hidden",
  zIndex: 100,
};
const exportMenuItemStyle = {
  padding: "10px 16px",
  cursor: "pointer",
  borderBottom: "1px solid #eee",
  transition: "background 0.2s",
};
