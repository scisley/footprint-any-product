// Define types for each agent's output

// Materials agent output
class MaterialsAgentOutput {
  details string              // Detailed text about materials analysis
  carbonScore float          // Carbon score (0-100)
  // Materials data
  materials MaterialInfo[]
  totalRecyclablePercentage float
  materialsRenewablePercentage float
}

class MaterialInfo {
  name string                // Material name (e.g., "Aluminum")
  percentage float          // Percentage of material in product
  carbonIntensity string     // Description of carbon intensity
  recyclability string       // Description of recyclability
  sourceInfo string          // Information about sourcing
}

// Manufacturing agent output
class ManufacturingAgentOutput {
  details string             // Detailed text about manufacturing analysis
  carbonScore float         // Carbon score (0-100)
  // Manufacturing data
  manufacturingLocations ManufacturingLocation[]
}

class ManufacturingLocation {
  country string
  city string
  facilityType string
  energySources string[]
  emissions string
  certifications string[]
}

// Packaging agent output
class PackagingAgentOutput {
  details string             // Detailed text about packaging analysis
  carbonScore float         // Carbon score (0-100)
  // Packaging data
  packagingMaterials PackagingMaterial[]
  packagingWeight string
  biodegradablePercentage float
}

class PackagingMaterial {
  material string
  percentage float
  recyclability string
  carbonFootprint string
  sourceInfo string
}

// Transport agent output
class TransportAgentOutput {
  details string             // Detailed text about transport analysis
  carbonScore float         // Carbon score (0-100)
  // Transport data
  primaryShippingRoutes ShippingRoute[]
  totalTransportEmissions string
}

class ShippingRoute {
  origin string
  destination string
  method string
  distance string
  emissionsPerUnit string
}

// Lifecycle agent output
class LifecycleAgentOutput {
  details string             // Detailed text about lifecycle analysis
  carbonScore float         // Carbon score (0-100)
  // Lifecycle data
  expectedLifespan string
  energyConsumption EnergyConsumption
  repairability Repairability
}

class EnergyConsumption {
  average string
  annualUsage string
  totalLifetimeEnergy string
  averageLifetimeEmissions string
}

class Repairability {
  score string
  limitations string[]
}

// End-of-life agent output
class EndOfLifeAgentOutput {
  details string             // Detailed text about end-of-life analysis
  carbonScore float         // Carbon score (0-100)
  // End-of-life data
  recyclability RecyclabilityInfo
  commonDisposalMethods map<string, string>  // Method to percentage
}

class RecyclabilityInfo {
  overallScore string
  componentsBreakdown ComponentsBreakdown
}

class ComponentsBreakdown {
  highlyRecyclable string[]
  hardToRecycle string[]
}

// Summary agent output
class SummaryAgentOutput {
  details string             // Detailed text about overall summary
  carbonScore float         // Carbon score (0-100)
  // Summary data
  totalCarbonFootprint TotalCarbonFootprint
  keyImpactAreas string[]
  positiveSustainabilityAspects string[]
  consumerRecommendation string
  sustainabilityImprovementPotential string
  similarProductsWithBetterScores string[]
  improvementRecommendations string[]
}

class TotalCarbonFootprint {
  score float
  classification string
  breakdown map<string, FootprintContribution>
  comparativeRanking string
}

class FootprintContribution {
  score float
  contribution string
}

// Materials Agent Function
function MaterialsAgent(productInfo: string) -> MaterialsAgentOutput {
  client "anthropic/claude-3-5-sonnet-20241022" // Use Claude for this example
  prompt #"
    You are the Materials Agent analyzing a product's material composition.
    
    The input could be a product name or a URL. If it's a product name, use your knowledge about 
    typical materials used in similar products to make reasonable estimates. If it's a URL, 
    analyze as if you could access the product details from that URL.
    
    Create a detailed analysis response with:
    - A 2-3 sentence summary about the product's materials for the "details" field
    - A carbon score between 0-100 (higher means higher environmental impact)
    - Material breakdown with percentages, carbon intensity, recyclability, and source information
    
    Product information:
    {{ productInfo }}

    Respond with a structured analysis following the output format.
    {{ ctx.output_format }}
  "#
}

// Manufacturing Agent Function
function ManufacturingAgent(productInfo: string) -> ManufacturingAgentOutput {
  client "anthropic/claude-3-5-sonnet-20241022"
  prompt #"
    You are the Manufacturing Agent analyzing a product's manufacturing process.
    
    The input could be a product name or a URL. If it's a product name, use your knowledge about 
    typical manufacturing processes for similar products to make reasonable estimates. If it's a URL, 
    analyze as if you could access the product details from that URL.
    
    Create a detailed analysis response with:
    - A 2-3 sentence summary about the product's manufacturing for the "details" field
    - A carbon score between 0-100 (higher means higher environmental impact)
    - Manufacturing locations with country, city, facility type, energy sources, emissions data, and certifications
    
    Product information:
    {{ productInfo }}

    Respond with a structured analysis following the output format.
    {{ ctx.output_format }}
  "#
}

// Packaging Agent Function
function PackagingAgent(productInfo: string) -> PackagingAgentOutput {
  client "anthropic/claude-3-5-sonnet-20241022"
  prompt #"
    You are the Packaging Agent analyzing a product's packaging.
    
    The input could be a product name or a URL. If it's a product name, use your knowledge about 
    typical packaging used for similar products to make reasonable estimates. If it's a URL, 
    analyze as if you could access the product details from that URL.
    
    First extract the product name or URL:
    - If the input contains "Product Name: [name]", use [name] as the product
    - If the input contains "Product URL: [url]", extract the product name from the URL
    - Otherwise use the entire input as the product name
    
    Create a detailed analysis response with:
    - A 2-3 sentence summary about the product's packaging for the "details" field, mentioning the product by name
    - A carbon score between 0-100 (higher means higher environmental impact)
    - Packaging materials with percentages, recyclability, carbon footprint, and source information specific to this type of product
    - Packaging weight and biodegradable percentage
    
    Consider the product type in your analysis:
    - Electronics typically use cardboard boxes, plastic films, foam padding
    - Clothing often uses cardboard boxes or plastic bags, tissue paper, tags
    - Furniture may use cardboard, plastic wrap, Styrofoam
    - Food/beverages use product-specific packaging (cans, bottles, boxes, etc.)
    
    Product information:
    {{ productInfo }}

    Respond with a structured analysis following the output format.
    {{ ctx.output_format }}
  "#
}

// Transport Agent Function
function TransportAgent(productInfo: string) -> TransportAgentOutput {
  client "anthropic/claude-3-5-sonnet-20241022"
  prompt #"
    You are the Transport Agent analyzing a product's transportation methods.
    
    The input could be a product name or a URL. If it's a product name, use your knowledge about 
    typical transport methods for similar products to make reasonable estimates. If it's a URL, 
    analyze as if you could access the product details from that URL.
    
    First extract the product name or URL:
    - If the input contains "Product Name: [name]", use [name] as the product
    - If the input contains "Product URL: [url]", extract the product name from the URL
    - Otherwise use the entire input as the product name
    
    Create a detailed analysis response with:
    - A 2-3 sentence summary about the product's transport for the "details" field, mentioning the product by name
    - A carbon score between 0-100 (higher means higher environmental impact)
    - Primary shipping routes with origin, destination, method, distance, and emissions data specific to this type of product
    - Total transport emissions
    
    Consider the product type in your analysis:
    - Electronics often ship from Asia (China, Taiwan, South Korea) to global markets via sea freight and then regional distribution
    - Clothing may come from Southeast Asia (Bangladesh, Vietnam, Cambodia) factories
    - Furniture might ship from manufacturing centers in Europe, North America or Asia
    - Food products often have regional processing and distribution networks
    
    Product information:
    {{ productInfo }}

    Respond with a structured analysis following the output format.
    {{ ctx.output_format }}
  "#
}

// Lifecycle Agent Function
function LifecycleAgent(productInfo: string) -> LifecycleAgentOutput {
  client "anthropic/claude-3-5-sonnet-20241022"
  prompt #"
    You are the Lifecycle Use Agent analyzing a product's usage lifecycle.
    
    The input could be a product name or a URL. If it's a product name, use your knowledge about 
    typical usage patterns and energy consumption for similar products to make reasonable estimates. If it's a URL, 
    analyze as if you could access the product details from that URL.
    
    First extract the product name or URL:
    - If the input contains "Product Name: [name]", use [name] as the product
    - If the input contains "Product URL: [url]", extract the product name from the URL
    - Otherwise use the entire input as the product name
    
    Create a detailed analysis response with:
    - A 2-3 sentence summary about the product's lifecycle use for the "details" field, mentioning the product by name
    - A carbon score between 0-100 (higher means higher environmental impact)
    - Expected lifespan specific to this type of product
    - Energy consumption details including average power use, annual usage, lifetime energy, and emissions
    - Repairability assessment with score and limitations specific to this product type
    
    Consider the product type in your analysis:
    - Electronics (like laptops, phones) typically have 3-5 year lifespans, moderate to high energy use, and limited repairability
    - Clothing items vary based on quality, wear frequency, and fashion trends
    - Furniture often has long lifespans (10+ years) with little to no energy use
    - Food/beverages have short lifespans with refrigeration or heating energy impacts
    
    Product information:
    {{ productInfo }}

    Respond with a structured analysis following the output format.
    {{ ctx.output_format }}
  "#
}

// End-of-Life Agent Function
function EndOfLifeAgent(productInfo: string) -> EndOfLifeAgentOutput {
  client "anthropic/claude-3-5-sonnet-20241022"
  prompt #"
    You are the End-of-Life Agent analyzing a product's disposal and recycling options.
    
    The input could be a product name or a URL. If it's a product name, use your knowledge about 
    typical end-of-life handling for similar products to make reasonable estimates. If it's a URL, 
    analyze as if you could access the product details from that URL.
    
    First extract the product name or URL:
    - If the input contains "Product Name: [name]", use [name] as the product
    - If the input contains "Product URL: [url]", extract the product name from the URL
    - Otherwise use the entire input as the product name
    
    Create a detailed analysis response with:
    - A 2-3 sentence summary about the product's end-of-life handling for the "details" field, mentioning the product by name
    - A carbon score between 0-100 (higher means higher environmental impact)
    - Recyclability assessment with overall score and components breakdown specific to this type of product
    - Common disposal methods with percentages specific to this product type
    
    Consider the product type in your analysis:
    - Electronics contain valuable but difficult to separate materials (metals, plastics, batteries, circuit boards)
    - Clothing varies by material type (natural fibers are more biodegradable than synthetics)
    - Furniture components have different recyclability (wood vs metal vs fabric vs plastic)
    - Food packaging varies widely in recyclability depending on specific materials
    
    Product information:
    {{ productInfo }}

    Respond with a structured analysis following the output format.
    {{ ctx.output_format }}
  "#
}

// Summary Agent Function
function SummaryAgent(productInfo: string) -> SummaryAgentOutput {
  client "anthropic/claude-3-5-sonnet-20241022"
  prompt #"
    You are the Summary Agent providing an overall assessment of a product's environmental impact.
    
    The input could be a product name or a URL. If it's a product name, use your knowledge about 
    similar products to make a comprehensive environmental impact assessment. If it's a URL, 
    analyze as if you could access the product details from that URL.
    
    First extract the product name or URL:
    - If the input contains "Product Name: [name]", use [name] as the product
    - If the input contains "Product URL: [url]", extract the product name from the URL
    - Otherwise use the entire input as the product name
    
    Create a detailed analysis response with:
    - A 3-4 sentence summary about the product's overall environmental impact for the "details" field, mentioning the product by name
    - A comprehensive carbon score between 0-100 (higher means higher environmental impact)
    - Total carbon footprint with breakdown by category specific to this type of product
    - Key impact areas specific to this product type
    - Positive sustainability aspects that might exist for this specific product
    - Consumer recommendations tailored to this product type
    - Sustainability improvement potential specific to this product
    - Similar products with better scores (provide realistic alternatives)
    - Improvement recommendations specific to this product category
    
    Consider the product type in your analysis:
    - Electronics have impacts from materials mining, energy-intensive manufacturing, and e-waste
    - Clothing has textile production impacts, chemical treatments, and fast fashion issues
    - Furniture has wood sourcing, manufacturing emissions, but potentially long lifespan
    - Food/beverages have agricultural, processing, refrigeration, and packaging impacts
    
    Product information:
    {{ productInfo }}

    Respond with a structured analysis following the output format.
    {{ ctx.output_format }}
  "#
}

// Test case for materials agent
test materials_agent {
  functions [MaterialsAgent]
  args {
    productInfo "Sample Laptop X1 - 14-inch laptop with aluminum chassis, lithium-ion battery, 16GB RAM, 512GB SSD, manufactured in Taiwan, packaged in cardboard and plastic."
  }
}

// Test case for manufacturing agent
test manufacturing_agent {
  functions [ManufacturingAgent]
  args {
    productInfo "Sample Laptop X1 - 14-inch laptop with aluminum chassis, lithium-ion battery, 16GB RAM, 512GB SSD, manufactured in Taiwan, packaged in cardboard and plastic."
  }
}

// Test case for packaging agent
test packaging_agent {
  functions [PackagingAgent]
  args {
    productInfo "Sample Laptop X1 - 14-inch laptop with aluminum chassis, lithium-ion battery, 16GB RAM, 512GB SSD, manufactured in Taiwan, packaged in cardboard and plastic."
  }
}

// Test case for transport agent
test transport_agent {
  functions [TransportAgent]
  args {
    productInfo "Sample Laptop X1 - 14-inch laptop with aluminum chassis, lithium-ion battery, 16GB RAM, 512GB SSD, manufactured in Taiwan, packaged in cardboard and plastic."
  }
}

// Test case for lifecycle agent
test lifecycle_agent {
  functions [LifecycleAgent]
  args {
    productInfo "Sample Laptop X1 - 14-inch laptop with aluminum chassis, lithium-ion battery, 16GB RAM, 512GB SSD, manufactured in Taiwan, packaged in cardboard and plastic."
  }
}

// Test case for end-of-life agent
test end_of_life_agent {
  functions [EndOfLifeAgent]
  args {
    productInfo "Sample Laptop X1 - 14-inch laptop with aluminum chassis, lithium-ion battery, 16GB RAM, 512GB SSD, manufactured in Taiwan, packaged in cardboard and plastic."
  }
}

// Test case for summary agent
test summary_agent {
  functions [SummaryAgent]
  args {
    productInfo "Sample Laptop X1 - 14-inch laptop with aluminum chassis, lithium-ion battery, 16GB RAM, 512GB SSD, manufactured in Taiwan, packaged in cardboard and plastic."
  }
}