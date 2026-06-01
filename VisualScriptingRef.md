# Visual Scripting Engine: Block Reference Guide

This reference details all structural nodes configured in the schema, split between execution entry points (**Events**) and programmatic operations (**Actions**).

---

## Events

Events act as root execution blocks. They trigger automatically when external or runtime state changes occur, opening an isolated variable scope below them.

| ID | Event Key | Visual/Text Representation | Inline Parameters | Scoped Output Variables (Given) | Functional Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0** | `LOADED` | `When website loaded...` | *None* | *None* | Fires immediately after the target webpage DOM and structural assets complete initialization. |
| **1** | `PRESSED` | `When [button] pressed...` | `button` (Object) | *None* | Triggers when the configured visual interface button receives a primary left mouse click. |
| **2** | `KEY_PRESSED` | `When [key] pressed...` | `key` (Key Type) | *None* | Listens globally or contextually for a physical hardware keystroke event matching the chosen key. |
| **3** | `MOUSE_ENTER` | `When mouse enters [object]...` | `object` (Object) | *None* | Fires once when the system cursor crosses the geometric boundary framework into a UI element. |
| **5** | `MOUSE_LEAVE` | `When mouse leaves [object]...` | `object` (Object) | *None* | Fires once when the system cursor exits the bounding area of a target visual element. |
| **6** | `FUNC_DEF` | `Define function [function]` | `function` (String) | Arguments mapped from call | Custom execution node declaration. Allocates a callback pointer bound to the function identifier. |
| **7** | `DONATION` | `When [donation] bought...` | `donation` (Object) | *None* | Triggers the exact moment an item checkout/donation element action is actively initialized. |
| **8** | `INPUT_SUBMIT` | `When [input] submitted...` | `input` (Object) | *None* | Fires when a user interacts with a text fields' confirm/return trigger key. |
| **9** | `MSG_RECEIVED` | `When message received...` | *None* | `{l!messageContent}`<br>`{l!messageSenderId}`<br>`{l!messageSenderName}` | Network event block firing upon reception of site-wide inter-process communications. |
| **10** | `CHANGED` | `When [object] changed...` | `object` (Object) | `{l!changedProperty}` | Listens for value updates or attribute adjustments occurring on a visual layout element. |
| **11** | `MOUSE_DOWN` | `When mouse down on [button]...` | `button` (Object) | *None* | Fires immediately when a click sequence transitions down over a target object. |
| **12** | `MOUSE_UP` | `When mouse up on [button]...` | `button` (Object) | *None* | Fires when a depressed mouse button is released anywhere inside or over the targeted boundary. |
| **13** | `RIGHT_CLICKED`| `When [button] right clicked...` | `button` (Object) | *None* | Listens for contextual alternate mouse button clicks matching the primary UI container node. |
| **14** | `CROSSSITE_MSG`| `When cross-site message received...`| *None* | `{l!sourceDomain}`<br>`{l!messageContent}`<br>`{l!messageSenderId}`<br>`{l!messageSenderName}` | Secure cross-domain event handler capturing data packets routed globally from distinct frames or pages. |
| **15** | `DONATION_COMPLETED`| `When donation completed...` | *None* | `{l!identifier}`<br>`{l!robuxAmount}`<br>`{l!purchasedNow}` | Asynchronous confirmation event executing when transaction queues settle across third-party safety verifications. |

---

## Actions

Actions run sequentially within event frames. They operate on internal script data, change visual properties, or modify system resources.

### Utility & Core System
* **LOG** (ID: `0`)
    * **Text Layout:** `Log [any]`
    * **Takes:** `any` (Any primitive or variable reference)
    * **Gives:** *None*
    * **Purpose:** Appends the target value to the runtime developer debugging console.
* **WARN** (ID: `1`)
    * **Text Layout:** `Warn [any]`
    * **Takes:** `any`
    * **Gives:** *None*
    * **Purpose:** Prints a high-visibility warning notification to logs.
* **ERROR** (ID: `2`)
    * **Text Layout:** `Error [any]`
    * **Takes:** `any`
    * **Gives:** *None*
    * **Purpose:** Halts code execution or logs severe issues into the error capture pipeline.
* **WAIT** (ID: `3`)
    * **Text Layout:** `Wait [number] seconds`
    * **Takes:** `number` (Duration value)
    * **Gives:** *None*
    * **Purpose:** Pauses processing along the current sequence line for the designated period.
* **NAV_REDIRECT** (ID: `4`)
    * **Text Layout:** `Redirect to [string]`
    * **Takes:** `string` (Target location URL)
    * **Gives:** *None*
    * **Purpose:** Instructs the application window context to load a specified destination address.

### Audio Management
* **AUDIO_PLAY** (ID: `5`)
    * **Text Layout:** `Play audio [id] → [variable?]`
    * **Takes:** `id` (Audio Asset identifier via Browser)
    * **Gives:** `variable?` (Optional dynamic text reference capturing the track handle pointer)
    * **Purpose:** Fires a single-shot playback instance of an asset file resource.
* **AUDIO_STOP_ALL** (ID: `7`)
    * **Text Layout:** `Stop all audio`
    * **Takes:** *None*
    * **Gives:** *None*
    * **Purpose:** Searches current active mixers and instantly forces termination of all sound processing.
* **AUDIO_PLAY_LOOP** (ID: `26`)
    * **Text Layout:** `Play looped audio [id] → [variable?]`
    * **Takes:** `id` (Audio asset)
    * **Gives:** `variable?` (Optional string tracker capturing container handle)
    * **Purpose:** Streams a sound resource configured to restart automatically on termination.
* **AUDIO_SET_VOL** (ID: `73`)
    * **Text Layout:** `Set volume of [variable] to [number]`
    * **Takes:** `variable` (Audio handle link), `number` (Gain level factor)
    * **Gives:** *None*
    * **Purpose:** Directly changes the gain amplitude processing of a running sound object.
* **AUDIO_STOP** (ID: `74`)
    * **Text Layout:** `Stop audio [variable]`
    * **Takes:** `variable` (Audio instance pointer)
    * **Gives:** *None*
    * **Purpose:** Deallocates an explicit streaming handle immediately.
* **AUDIO_PAUSE** (ID: `75`)
    * **Text Layout:** `Pause audio [variable]`
    * **Takes:** `variable` (Audio target marker)
    * **Gives:** *None*
    * **Purpose:** Suspends playback processing of a target track without scrubbing playhead timestamp.
* **AUDIO_RESUME** (ID: `76`)
    * **Text Layout:** `Resume audio [variable]`
    * **Takes:** `variable` (Paused audio handle link)
    * **Gives:** *None*
    * **Purpose:** Commands a suspended track playhead to resume data parsing from the saved index position.
* **AUDIO_SET_SPEED** (ID: `77`)
    * **Text Layout:** `Set speed of [variable] to [number]`
    * **Takes:** `variable` (Track handle pointer), `number` (Playback frequency adjustment scale)
    * **Gives:** *None*
    * **Purpose:** Modifies frequency playback speed (pitch/tempo scaling factor).

### Variables & Mathematical Operations
* **VAR_SET** (ID: `11`)
    * **Text Layout:** `Set [variable] to [any]`
    * **Takes:** `variable` (String pointer index), `any` (Content object data/primitive)
    * **Gives:** *None*
    * **Purpose:** Defines or overwrites standard application storage scope maps with incoming data payloads.
* **VAR_INC** (ID: `12`)
    * **Text Layout:** `Increase [variable] by [number]`
    * **Takes:** `variable` (Target name tracker), `number` (Value scale modifier)
    * **Gives:** *None*
    * **Purpose:** Performs addition step adjustment directly against an target tracking container.
* **VAR_DEC** (ID: `13`)
    * **Text Layout:** `Decrease [variable] by [number]`
    * **Takes:** `variable` (Target pointer key), `number` (Value decrement step size)
    * **Gives:** *None*
    * **Purpose:** Executes inline scalar subtraction against an established variable.
* **VAR_MUL** (ID: `14`)
    * **Text Layout:** `Multiply [variable] by [number]`
    * **Takes:** `variable` (Target address mapping), `number` (Scaling factor)
    * **Gives:** *None*
    * **Purpose:** Multiplies an existing stored tracking context by the numeric parameter.
* **VAR_DIV** (ID: `15`)
    * **Text Layout:** `Divide [variable] by [number]`
    * **Takes:** `variable` (Target storage lookup key), `number` (Divisor value)
    * **Gives:** *None*
    * **Purpose:** Divides variable data content in-place.
* **VAR_ROUND** (ID: `16`)
    * **Text Layout:** `Round [variable]`
    * **Takes:** `variable` (String name lookup link)
    * **Gives:** *None*
    * **Purpose:** Evaluates decimal values to the nearest matching whole integer.
* **VAR_FLOOR** (ID: `17`)
    * **Text Layout:** `Floor [variable]`
    * **Takes:** `variable` (Target field address map)
    * **Gives:** *None*
    * **Purpose:** Strips decimal components, shifting values downward to lower bound complete integers.
* **VAR_CEIL** (ID: `78`)
    * **Text Layout:** `Ceil [variable]`
    * **Takes:** `variable` (Numeric tracking value pointer)
    * **Gives:** *None*
    * **Purpose:** Forces evaluation upward to nearest ceiling mathematical value integer.
* **VAR_RANDOM** (ID: `27`)
    * **Text Layout:** `Set [var] to random [n] - [n]`
    * **Takes:** `var` (Destination address), `n` (Lower boundary integer), `n` (Upper bounds tracking threshold)
    * **Gives:** *None*
    * **Purpose:** Generates a pseudo-random value bound within constraints and registers it inside local variable context.
* **VAR_POW** (ID: `40`)
    * **Text Layout:** `Raise [variable] to the power of [number]`
    * **Takes:** `variable` (Base data pointer), `number` (Exponent modifier factor)
    * **Gives:** *None*
    * **Purpose:** Updates target variable content exponentially based on power inputs.
* **VAR_MOD** (ID: `41`)
    * **Text Layout:** `[variable] modulo [number]`
    * **Takes:** `variable` (Target data space lookup), `number` (Integer division divisor)
    * **Gives:** *None*
    * **Purpose:** Returns the remainder computation following integer operations.
* **VAR_DEL** (ID: `96`)
    * **Text Layout:** `Delete [variable]`
    * **Takes:** `variable` (Target index label tracking token)
    * **Gives:** *None*
    * **Purpose:** Purges mapped objects or registers explicitly from application state storage layout.
* **MATH_RUN** (ID: `114`)
    * **Text Layout:** `Run math function [function] [tuple] → [variable]`
    * **Takes:** `function` (Math operator name token), `tuple` (Argument parameter elements list)
    * **Gives:** `variable` (Calculation result destination string pointer)
    * **Purpose:** Passes complex data vectors into operational mathematical formulas (Trig/Log structures).

### Control Flow & Conditional Gateways
* **IF_EQ** (ID: `18`)
    * **Text Layout:** `If [any] is equal to [any]`
    * **Takes:** `any` (Left value operand), `any` (Right comparison operand)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Opens an execution fork if comparative balance checks match perfectly.
* **IF_NEQ** (ID: `19`)
    * **Text Layout:** `If [any] is not equal to [any]`
    * **Takes:** `any` (Left value), `any` (Right evaluation item)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Directs parsing pathways down internal blocks if value divergence is found.
* **IF_GT** (ID: `20`)
    * **Text Layout:** `If [any] is greater than [any]`
    * **Takes:** `any` (Left comparative parameter), `any` (Right value bounds constraint)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Checks whether values outpace evaluation thresholds.
* **IF_LT** (ID: `21`)
    * **Text Layout:** `If [any] is lower than [any]`
    * **Takes:** `any` (Target verification context), `any` (Boundary parameter check)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Verifies if left-hand data scales below baseline thresholds.
* **REPEAT** (ID: `22`)
    * **Text Layout:** `Repeat [number] times`
    * **Takes:** `number` (Integer limit boundary loop threshold count)
    * **Gives:** *Loop Block Execution Iteration Pointer*
    * **Purpose:** Clones process pathways down a linear loop cycle for a predefined count.
* **REPEAT_FOREVER** (ID: `23`)
    * **Text Layout:** `Repeat forever`
    * **Takes:** *None*
    * **Gives:** *Infinite Loop Pointer*
    * **Purpose:** Locks pipeline evaluation into a structural loop cycle requiring an explicit breakout signal.
* **BREAK** (ID: `24`)
    * **Text Layout:** `Break`
    * **Takes:** *None*
    * **Gives:** *None*
    * **Purpose:** Forces immediate evacuation out of the nearest structural looping block container.
* **END** (ID: `25`)
    * **Text Layout:** `end`
    * **Takes:** *None*
    * **Gives:** *None*
    * **Purpose:** Functional closure token bounding script loops, operations, or check definitions.
* **IF_CONTAINS** (ID: `37`)
    * **Text Layout:** `If [string] contains [string]`
    * **Takes:** `string` (Base target container data), `string` (Substring verification target)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Evaluates whether target text strings reside inside base structural content.
* **IF_NOT_CONTAINS** (ID: `38`)
    * **Text Layout:** `If [string] doesn't contain [string]`
    * **Takes:** `string` (Base text wrapper), `string` (Search marker string)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Verifies substring absence within text segments.
* **IF_AND** (ID: `44`)
    * **Text Layout:** `If [variable] AND [variable]`
    * **Takes:** `variable` (First evaluation conditional pointer), `variable` (Second logic verification gate)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Implements short-circuit evaluation needing all logic states validated true.
* **IF_OR** (ID: `45`)
    * **Text Layout:** `If [variable] OR [variable]`
    * **Takes:** `variable` (Logic target variable alpha), `variable` (Logic tracking gate beta)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Evaluates logical inclusive gates where at least one status verification flag equals true.
* **IF_NOR** (ID: `46`)
    * **Text Layout:** `If [variable] NOR [variable]`
    * **Takes:** `variable` (Logic check variable), `variable` (Evaluation target pointer)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Processes logical inversions requiring all conditional tracking lines to evaluate as false.
* **IF_XOR** (ID: `47`)
    * **Text Layout:** `If [variable] XOR [variable]`
    * **Takes:** `variable` (Operational state token A), `variable` (Operational state check B)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Enforces an exclusive logical balance configuration where exactly one flag must verify true.
* **IF_EXISTS** (ID: `92`)
    * **Text Layout:** `If [variable] exists`
    * **Takes:** `variable` (Object memory lookup string address)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Determines if memory spaces contain non-null reference definitions.
* **IF_NOT_EXISTS** (ID: `93`)
    * **Text Layout:** `If [variable] doesn't exist`
    * **Takes:** `variable` (Storage reference indexing label string)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Confirms if variables or properties are undeclared or unallocated.
* **IF_DARK_THEME** (ID: `108`)
    * **Text Layout:** `If dark theme enabled`
    * **Takes:** *None*
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Polls shell configurations to verify if dark visualization modes are enabled.
* **ELSE** (ID: `112`)
    * **Text Layout:** `else`
    * **Takes:** *None*
    * **Gives:** *Alternative Branch Flow Execution Pointer*
    * **Purpose:** Appends onto conditional gates to route execution when evaluation conditions collapse false.
* **IF_GTE** (ID: `125`)
    * **Text Layout:** `If [any] is greater or equal to [any]`
    * **Takes:** `any` (Primary tracking item), `any` (Boundary parameter check target)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Checks if left values meet or surpass the comparative boundaries.
* **IF_LTE** (ID: `126`)
    * **Text Layout:** `If [any] is lower or equal to [any]`
    * **Takes:** `any` (Operational tracking scale), `any` (Comparative threshold match value)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Validates whether metric vectors track under or match bounds limits.

### Object & Interface Property Manipulation
* **LOOK_HIDE** (ID: `8`)
    * **Text Layout:** `Make [object] invisible`
    * **Takes:** `object` (Element container)
    * **Gives:** *None*
    * **Purpose:** Sets layout display switches off, rendering an element completely invisible.
* **LOOK_SHOW** (ID: `9`)
    * **Text Layout:** `Make [object] visible`
    * **Takes:** `object` (Element tracking node)
    * **Gives:** *None*
    * **Purpose:** Resets rendering attributes on hidden entities to make them visible.
* **LOOK_SET_TEXT** (ID: `10`)
    * **Text Layout:** `Set [object] text to [string]`
    * **Takes:** `object` (Target UI element container), `string` (Plain text block)
    * **Gives:** *None*
    * **Purpose:** Directly replaces text content within label or layout boundaries.
* **LOOK_SET_PROP** (ID: `31`)
    * **Text Layout:** `Set [property] of [object] to [any]`
    * **Takes:** `property` (Attribute key string), `object` (UI target element pointer), `any` (Value parameter settings)
    * **Gives:** *None*
    * **Purpose:** Overrides target rendering configurations (Colors, positions, opacity dimensions).
* **LOOK_GET_PROP** (ID: `39`)
    * **Text Layout:** `Get [property] of [object] → [variable]`
    * **Takes:** `property` (Attribute query keyword name), `object` (Target element structural container)
    * **Gives:** `variable` (Output storage reference label string location)
    * **Purpose:** Polls rendering attributes from runtime graphics frames and outputs them into storage.
* **LOOK_DUPLICATE** (ID: `49`)
    * **Text Layout:** `Duplicate [object] → [variable]`
    * **Takes:** `object` (Target container UI module block structure)
    * **Gives:** `variable` (Target dynamic tracker link name text string)
    * **Purpose:** Instantiates an exact replica node tracking matrix reference copy into active scenes.
* **LOOK_DELETE** (ID: `50`)
    * **Text Layout:** `Delete [object]`
    * **Takes:** `object` (Scene container engine link instance)
    * **Gives:** *None*
    * **Purpose:** Deallocates and purges visual modules from layout hierarchies permanently.
* **LOOK_TWEEN** (ID: `88`)
    * **Text Layout:** `Tween [property] of [object] to [any] - [time] [style] [direction]`
    * **Takes:** `property` (Target modifier field string), `object` (Visual layout component), `any` (Target value destination parameter), `time` (Duration parameter), `style` (Interpolation curve type token), `direction` (Phasing direction)
    * **Gives:** *None*
    * **Purpose:** Smoothly animates property changes over time using custom easing curves.
* **LOOK_SET_IMG** (ID: `106`)
    * **Text Layout:** `Set [object] image to [id]`
    * **Takes:** `object` (Graphic display block element container), `id` (Image configuration map token)
    * **Gives:** *None*
    * **Purpose:** Switches bitmap source files rendering over targeted graphical interfaces.
* **LOOK_SET_AVATAR** (ID: `107`)
    * **Text Layout:** `Set [object] image to avatar of [userid] [resolution?]`
    * **Takes:** `object` (Visual presentation container target), `userid` (Target user profile ID number parameter), `resolution?` (Optional size dimensions string)
    * **Gives:** *None*
    * **Purpose:** Automatically resolves profile reference URLs to draw current platform avatars onto layouts.
* **LOOK_GET_AT_POS** (ID: `127`)
    * **Text Layout:** `Get objects at position [x] [y] → [array]`
    * **Takes:** `x` (Coordinate scale data string pointer), `y` (Vertical plane metric marker)
    * **Gives:** `array` (Table name registry destination array containing found items references)
    * **Purpose:** Runs raycasts or coordinate collision checks to gather objects positioned over precise layout boundaries.
* **LOOK_GET_ASSET_INFO** (ID: `129`)
    * **Text Layout:** `Get [info] of asset [id] → [variable]`
    * **Takes:** `info` (Metadata metric category name string), `id` (Target global resource file reference ID)
    * **Gives:** `variable` (Output variable identifier destination marker text)
    * **Purpose:** Extract catalog metadata from online registry storage caches.

### Data Manipulation & Input Extraction
* **INPUT_GET_TEXT** (ID: `30`)
    * **Text Layout:** `Get text from [input] → [variable]`
    * **Takes:** `input` (Target interactive text module block container node)
    * **Gives:** `variable` (Destination variable name)
    * **Purpose:** Captures text content entered by users within field containers.
* **INPUT_GET_VIEWPORT** (ID: `84`)
    * **Text Layout:** `Get viewport size → [x] [y]`
    * **Takes:** *None*
    * **Gives:** `x` (Width tracker variable mapping label name), `y` (Height pixel tracking coordinate space)
    * **Purpose:** Polls active browser bounds dimensions to acquire current display size variables.
* **INPUT_GET_CURSOR** (ID: `85`)
    * **Text Layout:** `Get cursor position → [x] [y]`
    * **Takes:** *None*
    * **Gives:** `x` (Horizontal axis location pointer name), `y` (Vertical coordinate registration variable marker)
    * **Purpose:** Maps cursor position to screen coordinate pixel vectors.

### Network Broadcasting
* **NET_BROADCAST_PAGE** (ID: `32`)
    * **Text Layout:** `Broadcast [message] across page`
    * **Takes:** `message` (Data string contents payload)
    * **Gives:** *None*
    * **Purpose:** Fires inter-frame scripts messaging lines targeting all containers running inside the exact same local page.
* **NET_BROADCAST_SITE** (ID: `33`)
    * **Text Layout:** `Broadcast [message] across site`
    * **Takes:** `message` (Data string payload packet text)
    * **Gives:** *None*
    * **Purpose:** Transmits event notification vectors targeting listener routines configured active across any site module.
* **NET_BROADCAST_CROSSSITE** (ID: `130`)
    * **Text Layout:** `Broadcast [message] cross-site to [page]`
    * **Takes:** `message` (Data payload content), `page` (Target reference destination address tracker)
    * **Gives:** *None*
    * **Purpose:** Routes a network data message line safely to an explicit cross-domain layout target listener gateway.

### Browser Cookies Storage
* **COOKIE_SET** (ID: `34`)
    * **Text Layout:** `Set [cookie] to [any]`
    * **Takes:** `cookie` (Key text identifier), `any` (Information block payload)
    * **Gives:** *None*
    * **Purpose:** Commits tracking records persistently into local client browser session partitions.
* **COOKIE_INC** (ID: `35`)
    * **Text Layout:** `Increase [cookie] by [number]`
    * **Takes:** `cookie` (Persistent tracking index marker string), `number` (Scalar modifier size step)
    * **Gives:** *None*
    * **Purpose:** Accesses, updates, and writes incremented numbers back into a saved client storage key.
* **COOKIE_GET** (ID: `36`)
    * **Text Layout:** `Get cookie [cookie] → [variable]`
    * **Takes:** `cookie` (Browser memory data mapping token address string)
    * **Gives:** `variable` (Destination storage label pointer index name)
    * **Purpose:** Recovers persistent text logs stored within browser sandboxes.
* **COOKIE_DEL** (ID: `62`)
    * **Text Layout:** `Delete cookie [cookie]`
    * **Takes:** `cookie` (Saved browser state registry tracking index name string)
    * **Gives:** *None*
    * **Purpose:** Unsets and purges target session keys out of browser storage partitions.

### String Processing Operations
* **STR_SUB** (ID: `42`)
    * **Text Layout:** `Sub [variable] [start] - [end]`
    * **Takes:** `variable` (Target text storage location registry address), `start` (Zero-indexed character start point), `end` (Character extraction terminal point indicator)
    * **Gives:** *None*
    * **Purpose:** Truncates or extracts targeted substring sequences in place on a chosen variable reference.
* **STR_REPLACE** (ID: `43`)
    * **Text Layout:** `Replace [string] in [variable] by [string]`
    * **Takes:** `string` (Target search expression token text), `variable` (Modifiable tracking string location), `string` (Replacement character pattern text block)
    * **Gives:** *None*
    * **Purpose:** Scans target text vectors and replaces text segments matching search parameters.
* **STR_LEN** (ID: `48`)
    * **Text Layout:** `Get length of [string] → [variable]`
    * **Takes:** `string` (Input evaluation string array data text)
    * **Gives:** `variable` (Output variable identifier destination marker text)
    * **Purpose:** Calculates total string character lengths and populates destination spaces.
* **STR_SPLIT** (ID: `57`)
    * **Text Layout:** `Split [string] [separator] → [table]`
    * **Takes:** `string` (Source data block segment text), `separator` (Delimiter pattern string)
    * **Gives:** `table` (Destination array list pointer mapping registry name string)
    * **Purpose:** Breaks text segments apart using a delimiter and converts them into structured tables.
* **STR_LOWER** (ID: `69`)
    * **Text Layout:** `Lower [string] → [variable]`
    * **Takes:** `string` (Alpha data character target sequence)
    * **Gives:** `variable` (Output variable string target index identifier name)
    * **Purpose:** Converts alphabetical components to lowercase formatting.
* **STR_UPPER** (ID: `70`)
    * **Text Layout:** `Upper [string] → [variable]`
    * **Takes:** `string` (Input alpha target stream processing text)
    * **Gives:** `variable` (Output variable storage registration identification index)
    * **Purpose:** Converts alphabetical components to uppercase formatting.
* **STR_CONCAT** (ID: `109`)
    * **Text Layout:** `Concatenate [string] with [string] → [variable]`
    * **Takes:** `string` (Prefix value data segment text), `string` (Suffix text block segment metadata)
    * **Gives:** `variable` (Target variable location output token designation label)
    * **Purpose:** Merges two strings into a unified text string.

### User Data Retrieval
* **USER_GET_NAME** (ID: `51`)
    * **Text Layout:** `Get local username → [variable]`
    * **Takes:** *None*
    * **Gives:** `variable` (Destination storage locator mapping address name label)
    * **Purpose:** Fetches unique platform account name handles from session indices.
* **USER_GET_ID** (ID: `52`)
    * **Text Layout:** `Get local user ID → [variable]`
    * **Takes:** *None*
    * **Gives:** `variable` (Target application storage allocation key name label string)
    * **Purpose:** Retrieves the platform account profile ID integer value.
* **USER_GET_DISPLAY** (ID: `53`)
    * **Text Layout:** `Get local display name → [variable]`
    * **Takes:** *None*
    * **Gives:** `variable` (Target tracking assignment pointer label space text string)
    * **Purpose:** Captures profile display name strings from the client frame.

### Tables & Arrays Manipulation
* **TABLE_CREATE** (ID: `54`)
    * **Text Layout:** `Create table [table]`
    * **Takes:** `table` (Target index label tracking token variable name)
    * **Gives:** *None*
    * **Purpose:** Instantiates an empty, addressable map array into variable registers.
* **TABLE_SET** (ID: `55`)
    * **Text Layout:** `Set entry [entry] of [table] to [any]`
    * **Takes:** `entry` (Index position key indicator identifier text), `table` (Target active collection map pointer), `any` (Data payload item contents)
    * **Gives:** *None*
    * **Purpose:** Adds or modifies entry values under specific mapping keys within an active collection array.
* **TABLE_GET** (ID: `56`)
    * **Text Layout:** `Get entry [entry] of [table] → [variable]`
    * **Takes:** `entry` (Index or associative lookup indicator keyword string), `table` (Source collection dataset map array space identifier)
    * **Gives:** `variable` (Destination variable registry pointer tracking name)
    * **Purpose:** Extracts stored entries from specific keys or indices inside arrays.
* **TABLE_LEN** (ID: `59`)
    * **Text Layout:** `Get length of [array] → [variable]`
    * **Takes:** `array` (Target data collection lookup map identity pointer)
    * **Gives:** `variable` (Output tracking storage container destination field name)
    * **Purpose:** Returns the total element count stored within an array structure.
* **TABLE_SET_OBJ** (ID: `66`)
    * **Text Layout:** `Set entry [entry] of [table] to [object]`
    * **Takes:** `entry` (Index marker key identification name), `table` (Target map database collection space index pointer), `object` (Visual module reference framework container)
    * **Gives:** *None*
    * **Purpose:** Caches interface element links safely within array entries.
* **TABLE_INSERT** (ID: `89`)
    * **Text Layout:** `Insert [any] at position [number?] of [array]`
    * **Takes:** `any` (Data context record payload), `number?` (Optional insertion index position), `array` (Target database catalog collection storage mapping)
    * **Gives:** *None*
    * **Purpose:** Injects a data item at a specific index location in an array, shifting subsequent entries upward.
* **TABLE_DEL** (ID: `90`)
    * **Text Layout:** `Delete entry [entry] of [table]`
    * **Takes:** `entry` (Associative map index text string key item), `table` (Target active layout array identifier)
    * **Gives:** *None*
    * **Purpose:** Erases individual associative key entries out of targeted table structures.
* **TABLE_REMOVE** (ID: `91`)
    * **Text Layout:** `Remove entry at position [number?] of [array]`
    * **Takes:** `number?` (Target array location removal sequence pointer index), `array` (Target layout listing data map space indicator string)
    * **Gives:** *None*
    * **Purpose:** Completely deallocates sequential index numbers from list configurations, shifting trailing indexes downward.
* **TABLE_JOIN** (ID: `110`)
    * **Text Layout:** `Join [array] using [string] → [variable]`
    * **Takes:** `array` (Source array lookup list identification key name), `string` (Character string separator delimiter format), `variable` (Unified output token reference identity text label)
    * **Gives:** *None*
    * **Purpose:** flattens whole arrays into a single continuous text variable block split via custom separators.
* **TABLE_ITER** (ID: `113`)
    * **Text Layout:** `Iterate through [table] ({l!index},{l!value})`
    * **Takes:** `table` (Source processing data array key identifier text location name)
    * **Gives:** *Loop Step Context Scope* (Sets local index and value elements per step loop sequence cycle)
    * **Purpose:** For-each iterator node parsing through every entry present within a targeted table.

### Structural UI Hierarchy Management
* **HIER_PARENT** (ID: `58`)
    * **Text Layout:** `Parent [object] under [object]`
    * **Takes:** `object` (Target downstream child container node), `object` (New upstream layout parent master layout container framework)
    * **Gives:** *None*
    * **Purpose:** Changes layout architecture nesting properties, altering layout inheritance paths.
* **HIER_GET_PARENT** (ID: `97`)
    * **Text Layout:** `Get parent of [object] → [variable]`
    * **Takes:** `object` (Target layout child system reference unit)
    * **Gives:** `variable` (Output memory reference space variable address indicator text string)
    * **Purpose:** Traverses structural layers directly upward to discover the immediately nested container link wrapper.
* **HIER_FIND_ANCESTOR** (ID: `98`)
    * **Text Layout:** `Find ancestor named [string] in [object] → [variable]`
    * **Takes:** `string` (Target search identification key label text match identifier name), `object` (Starting node position context reference layout element container)
    * **Gives:** `variable` (Output container location string key identity tracking register name)
    * **Purpose:** Recursively crawls upward to locate target containers matching text identity tags.
* **HIER_FIND_CHILD** (ID: `99`)
    * **Text Layout:** `Find child named [string] in [object] → [variable]`
    * **Takes:** `string` (Search term name keyword configuration criteria string), `object` (Parent root node structural start vector location container layout element)
    * **Gives:** `variable` (Output element data reference mapping variable registration key tag text name)
    * **Purpose:** Searches immediate first-tier downstream children nodes for matching text target designations.
* **HIER_FIND_DESCENDANT** (ID: `100`)
    * **Text Layout:** `Find descendant named [string] in [object] → [variable]`
    * **Takes:** `string` (Target identification name text string key identifier parameter tracking format), `object` (Root ancestor structural context start pointer coordinate visual container layout)
    * **Gives:** `variable` (Destination storage data link variable tracker classification indicator tag text)
    * **Purpose:** Deeply crawls downward through nested layer child nodes to find matching target layout modules.
* **HIER_GET_CHILDREN** (ID: `101`)
    * **Text Layout:** `Get children of [object] → [table]`
    * **Takes:** `object` (Source master element structural anchor link boundary layout container block)
    * **Gives:** `table` (Destination compilation dictionary list index array variable tracking address label name text)
    * **Purpose:** Compiles direct immediate first-level sub-node references down into a table index array collection list format.
* **HIER_GET_DESCENDANTS** (ID: `102`)
    * **Text Layout:** `Get descendants of [object] → [table]`
    * **Takes:** `object` (Root hierarchy component element container target system layout tracking module anchor link)
    * **Gives:** `table` (Destination variable catalog map database text string indicator storage reference label mapping space name)
    * **Purpose:** Runs deep structural tree sweeps, compiling every sub-node link down the tree into an addressable list dataset array configuration table.

### Context Layout Validation Gates
* **IF_IS_ANCESTOR** (ID: `103`)
    * **Text Layout:** `If [object] is ancestor of [object]`
    * **Takes:** `object` (Upstream context match validation tracking layout component check), `object` (Downstream validation structural nested target element container block module)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Verifies deep upward layout parent nesting paths exist across compared layout objects.
* **IF_IS_CHILD** (ID: `104`)
    * **Text Layout:** `If [object] is child of [object]`
    * **Takes:** `object` (Target check item structural container wrapper block), `object` (Expected direct parent framework module location container design unit)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Checks direct first-tier parent nesting alignments between comparative parameters.
* **IF_IS_DESCENDANT** (ID: `105`)
    * **Text Layout:** `If [object] is descendant of [object]`
    * **Takes:** `object` (Target verification tracking downstream node layout module container block item), `object` (Expected master source baseline ancestor container block design component element tracking link)
    * **Gives:** *Conditional Scope Entry*
    * **Purpose:** Runs validation checks down entire sub-tree paths to see if elements descend from target structural points.

### Advanced Variables Operations
* **AVAR_SET** (ID: `94`)
    * **Text Layout:** `Set [property] of [variable] to [any]`
    * **Takes:** `property` (Target dictionary data key string name entry keyword mapping assignment label), `variable` (Target complex compound map storage variable context tracking address locator identifier), `any` (Data payload content entity parameter layout structure assignment metric value)
    * **Gives:** *None*
    * **Purpose:** Writes data directly into fields nested on custom structured object variables.
* **AVAR_GET** (ID: `95`)
    * **Text Layout:** `Get [property] of [variable] → [variable]`
    * **Takes:** `property` (Target sub-field lookup configuration identity entry string keyword mapping identifier index text), `variable` (Source structured complex object collection data register pointer map block track location name string)
    * **Gives:** `variable` (Destination storage variable assignment tracking designation output identifier index key label address)
    * **Purpose:** Extracts values out of sub-fields nested within complex custom structural variables.

### Time & Processing Calendars
* **TIME_GET_UNIX** (ID: `68`)
    * **Text Layout:** `Get unix timestamp → [variable]`
    * **Takes:** *None*
    * **Gives:** `variable` (Target assignment indicator output text string variable locator key label mapping destination name)
    * **Purpose:** Captures standard local Unix timestamp integers tracking milliseconds spent since Epoch times scales.
* **TIME_GET_SERVER_UNIX** (ID: `116`)
    * **Text Layout:** `Get server unix timestamp → [variable]`
    * **Takes:** *None*
    * **Gives:** `variable` (Output variable identifier name label destination text data locator tracking register index mapping link address)
    * **Purpose:** Queries server nodes directly to fetch synchronized unified clock stamps bypassing local machine alterations.
* **TIME_FORMAT_NOW** (ID: `71`)
    * **Text Layout:** `Format current date/time [format] → [variable]`
    * **Takes:** `format` (String pattern parsing rule sequence instruction formatting profile layout config text), `variable` (Output string identifier label tracking context assignment register link destination name)
    * **Gives:** *None*
    * **Purpose:** Converts active local clock vectors straight into clean structured layout presentation strings using custom tokens.
* **TIME_FORMAT_UNIX** (ID: `72`)
    * **Text Layout:** `Format from unix [number] [format] → [variable]`
    * **Takes:** `number` (Raw source input integer timestamp configuration metrics context), `format` (String formatting rule structure pattern token tracking criteria setup profiles), `variable` (Output string data registry tracking identifier label pointer mapping address name link)
    * **Gives:** *None*
    * **Purpose:** Formats raw timestamp numbers into reader-friendly date-time string variants.
* **TIME_GET_TIMEZONE** (ID: `118`)
    * **Text Layout:** `Get timezone → [variable]`
    * **Takes:** *None*
    * **Gives:** `variable` (Output text data value memory registration variable mapping identity designation label space text index link)
    * **Purpose:** Polls operating environments to extract regional offset tracking indicators.
* **TIME_GET_TICK** (ID: `83`)
    * **Text Layout:** `Get tick → [variable]`
    * **Takes:** *None*
    * **Gives:** `variable` (Output target locator pointer definition name string text identity tracking register map assignment indicator label)
    * **Purpose:** Returns precise machine tick vectors tracking program runtime scales.

### Browser Navigation Parameters
* **NAV_GET_QUERY** (ID: `67`)
    * **Text Layout:** `Get query string parameter [string] → [variable]`
    * **Takes:** `string` (URL search query index lookup key designation target label classification tracking format phrase text pattern), `variable` (Output storage variable indexing identity address registration pointer identifier mapping name indicator label text)
    * **Gives:** *None*
    * **Purpose:** Parses target browser addresses to pull URL parameter values directly out of active navigation search query indicators.
* **NAV_GET_URL** (ID: `117`)
    * **Text Layout:** `Get URL → [variable]`
    * **Takes:** *None*
    * **Gives:** `variable` (Output storage space tracking identification index pointer text string mapping address locator assignment key label)
    * **Purpose:** Resolves absolute text addresses tracking active web layout views.

### Graphics Color Format Engineering
* **COLOR_HEX_TO_RGB** (ID: `119`)
    * **Text Layout:** `Convert [hex] to RGB → [variable]`
    * **Takes:** `hex` (Base hexadecimal color system data payload sequence string indicator tracking token character array code), `variable` (Output tracking storage container field name label text variable registration identification pointer mapping index address location)
    * **Gives:** *None*
    * **Purpose:** Splits programmatic hex color entries out into multi-channel numeric vector arrays tracking Red, Green, and Blue factors.
* **COLOR_HEX_TO_HSV** (ID: `120`)
    * **Text Layout:** `Convert [hex] to HSV → [variable]`
    * **Takes:** `hex` (Source target hexadecimal notation profile config verification identifier string character value format), `variable` (Output tracking registration identification mapping pointer space label text string data variable location indicator address)
    * **Gives:** *None*
    * **Purpose:** Translates hex notation strings over into Hue, Saturation, and Value numeric metrics layout spaces.
* **COLOR_RGB_TO_HEX** (ID: `121`)
    * **Text Layout:** `Convert [RGB] to hex → [variable]`
    * **Takes:** `RGB` (Source channels composite text code array format mapping metrics string parameters data), `variable` (Output target destination variable locator text string label mapping space token register address location identity)
    * **Gives:** *None*
    * **Purpose:** Compiles multi-channel numeric RGB data packages into clean unified hex strings.
* **COLOR_HSV_TO_HEX** (ID: `122`)
    * **Text Layout:** `Convert [HSV] to hex → [variable]`
    * **Takes:** `HSV` (Source structural color dimension channels index map scale composite string parameter data metrics), `variable` (Output identifier location tracking destination variable token register space assignment pointer label name text)
    * **Gives:** *None*
    * **Purpose:** Compiles Hue, Saturation, and Value channel arrays back into single standard hex string profiles.
* **COLOR_LERP** (ID: `123`)
    * **Text Layout:** `Lerp [hex] to [hex] by [alpha] → [variable]`
    * **Takes:** `hex` (Origin system baseline starting color value code payload string parameter configuration metric), `hex` (Terminal destination endpoint target vector profile boundary layout setting configuration string color value code code), `alpha` (Interpolation step factor modifier ratio scalar percentile progress decimal tracking parameter configuration size), `variable` (Output data storage space mapping identity text token register pointer index label address locator assignment name)
    * **Gives:** *None*
    * **Purpose:** Calculates linear interpolation blend results between two color metrics configurations using matching scalar alpha steps.

### Custom Functions Code Blocks Execution
* **FUNC_RUN** (ID: `87`)
    * **Text Layout:** `Run function [function] [tuple] → [variable?]`
    * **Takes:** `function` (Target callback routine structural key design token identification index name layout text string address locator), `tuple` (Parameters value argument listing entry data set tuple structure tracking configuration array maps framework link data), `variable?` (Optional callback return storage space alignment assignment locator tracking identity register name indicator label string text pointer)
    * **Gives:** *None*
    * **Purpose:** Executes pre-allocated internal callback routines, supporting return variables.
* **FUNC_RUN_PROTECTED** (ID: `128`)
    * **Text Layout:** `Run protected function [function] [tuple] → [success_variable?] [variable?]`
    * **Takes:** `function` (Target execution callback pointer address routine definition registry token index identifier map text name label layout), `tuple` (Parameters configuration argument payload value matrix sequence listings vector array container table element reference data tracking system framework link links), `success_variable?` (Optional block safety confirmation tracking catch flag state outcome validation boolean result mapping space label name text string register locator pointer tracking address location data), `variable?` (Optional dynamic payload calculation value data tracking index output reference pointer assignment structural container layout field address mapping registration name label string text index link locator token)
    * **Gives:** *None*
    * **Purpose:** Runs custom subroutines inside safety isolation blocks. Catches exceptions to prevent application crashes.
* **RETURN** (ID: `115`)
    * **Text Layout:** `Return [any]`
    * **Takes:** `any` (Output transaction product processing calculation metrics context value data payload asset reference document file block model element text string array collection dictionary map list setup tracking indicator token metadata register pointer)
    * **Gives:** *None*
    * **Purpose:** Exits custom function code blocks, passing specified data payloads back to the caller block.

### Explanatory Code Annotations
* **COMMENT** (ID: `124`)
    * **Text Layout:** `[comment]`
    * **Takes:** `comment` (Inert explanatory plain text description notes logs data records information strings layout text phrasing paragraphs words phrases character arrays sentences matching baseline metadata)
    * **Gives:** *None*
    * **Purpose:** Creates a non-executing visual card within script files used for developer documentation.