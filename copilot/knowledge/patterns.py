"""Coding interview patterns: how to recognise each one and what to say."""

PATTERNS = [
    {"id": "hashmap", "name": "Hash Map",
     "signal": "Need lookup, count, or complement in O(1)",
     "complexity": "O(n)", "ask": "What do I wish I had already seen?",
     "model": "Trade space for time. 'Have I seen this before?' or 'how many "
              "of these?' becomes O(1) once you store it.",
     "recognize": ["frequency", "count", "duplicate", "complement",
                   "target sum", "group by", "anagram", "dedupe"],
     "template": "seen = {}\nfor i, x in enumerate(nums):\n"
                 "    if target - x in seen:\n"
                 "        return [seen[target - x], i]\n"
                 "    seen[x] = i",
     "mistakes": ["Writing to the map before checking it (self-match)",
                  "A list where a set would do turns O(n) into O(n^2)"],
     "say": "One pass with a hash map of values already seen. Each lookup "
            "is O(1), so O(n) time and O(n) space instead of O(n^2).",
     "examples": ["Two Sum", "Group Anagrams",
                  "Longest Consecutive Sequence", "Contains Duplicate"]},
    {"id": "twoptr", "name": "Two Pointers",
     "signal": "Sorted array, or a pair/triplet from opposite ends",
     "complexity": "O(n) after sort", "ask": "Can I safely discard one end?",
     "model": "Two indices walk toward each other. Each step provably "
              "eliminates one candidate.",
     "recognize": ["sorted", "pair", "triplet", "palindrome", "container",
                   "partition in place", "3sum"],
     "template": "l, r = 0, len(nums) - 1\nwhile l < r:\n"
                 "    s = nums[l] + nums[r]\n"
                 "    if s == target: return [l, r]\n"
                 "    if s < target: l += 1\n    else: r -= 1",
     "mistakes": ["Forgetting to sort first",
                  "Not skipping duplicates in 3Sum"],
     "say": "Because it's sorted, the sum at the two ends tells me which "
            "pointer to move, so I discard one element per step: O(n).",
     "examples": ["Two Sum II", "3Sum", "Container With Most Water",
                  "Valid Palindrome"]},
    {"id": "fastslow", "name": "Fast & Slow Pointers",
     "signal": "Cycle detection, or the middle of a list in one pass",
     "complexity": "O(n), O(1) space", "ask": "Can two speeds meet?",
     "model": "One pointer moves twice as fast. With a cycle they meet; "
              "without one, fast hits the end when slow is at the middle.",
     "recognize": ["cycle", "middle of", "linked list", "kth from end",
                   "happy number", "repeated state"],
     "template": "slow = fast = head\nwhile fast and fast.next:\n"
                 "    slow, fast = slow.next, fast.next.next\n"
                 "    if slow is fast: return True\nreturn False",
     "mistakes": ["Checking fast.next.next before fast.next",
                  "Off-by-one on the middle for even lengths"],
     "say": "Two pointers at different speeds: if there's a cycle the fast "
            "one laps the slow one. O(n) time, O(1) space.",
     "examples": ["Linked List Cycle", "Middle of the Linked List",
                  "Remove Nth Node From End", "Reorder List"]},
    {"id": "window", "name": "Sliding Window",
     "signal": "Longest/shortest contiguous range under a constraint",
     "complexity": "O(n)", "ask": "Can I maintain a valid window?",
     "model": "Keep a moving [left, right] range instead of re-examining "
              "overlapping subarrays. Each element enters and leaves once.",
     "recognize": ["contiguous", "substring", "subarray", "longest",
                   "shortest", "at most k", "without repeating", "window"],
     "template": "left = best = 0\ncount = {}\n"
                 "for right, ch in enumerate(s):\n"
                 "    count[ch] = count.get(ch, 0) + 1\n"
                 "    while invalid(count):\n"
                 "        count[s[left]] -= 1; left += 1\n"
                 "    best = max(best, right - left + 1)",
     "mistakes": ["Updating the answer before the window is valid again",
                  "Using if where you need while to shrink"],
     "say": "Expand the right edge; when the window breaks the constraint, "
            "shrink from the left until valid, then record the best. O(n).",
     "examples": ["Longest Substring Without Repeating Characters",
                  "Minimum Window Substring",
                  "Longest Repeating Character Replacement"]},
    {"id": "prefix", "name": "Prefix Sum",
     "signal": "Repeated range sums, or subarrays summing to K",
     "complexity": "O(n) build, O(1) query",
     "ask": "Can I precompute cumulative totals?",
     "model": "Running totals turn any range sum into one subtraction. With "
              "a hash map it counts subarrays summing to K in one pass.",
     "recognize": ["range sum", "sum between", "subarray sum equals",
                   "running balance", "equilibrium"],
     "template": "seen = {0: 1}\ntotal = count = 0\nfor x in nums:\n"
                 "    total += x\n    count += seen.get(total - k, 0)\n"
                 "    seen[total] = seen.get(total, 0) + 1",
     "mistakes": ["Forgetting the {0: 1} seed",
                  "Inclusive vs exclusive off-by-one"],
     "say": "A subarray sums to k exactly when the current prefix minus k "
            "has been seen before, so one pass with a map gives the count.",
     "examples": ["Subarray Sum Equals K", "Product of Array Except Self",
                  "Range Sum Query", "Contiguous Array"]},
    {"id": "bsearch", "name": "Binary Search",
     "signal": "Sorted input, or a monotonic yes/no answer space",
     "complexity": "O(log n)", "ask": "Is the predicate monotonic?",
     "model": "Halve the space each step. The powerful version searches the "
              "answer space when 'is X feasible?' flips once.",
     "recognize": ["sorted", "rotated", "first occurrence", "minimum capacity",
                   "minimum speed", "such that", "log n", "search"],
     "template": "lo, hi = 1, max(c)\nwhile lo < hi:\n"
                 "    mid = (lo + hi) // 2\n"
                 "    if feasible(mid): hi = mid\n    else: lo = mid + 1\n"
                 "return lo",
     "mistakes": ["Infinite loop from lo = mid",
                  "Mixing < and <= between template styles"],
     "say": "The predicate is monotonic, so I binary search the answer "
            "space: O(log range) times the feasibility check.",
     "examples": ["Binary Search", "Search in Rotated Sorted Array",
                  "Koko Eating Bananas"]},
    {"id": "stack", "name": "Stack",
     "signal": "Nested structure, or the most recent unresolved thing",
     "complexity": "O(n)", "ask": "Does the last thing opened close first?",
     "model": "Last in, first out: when the most recent item is the one you "
              "need next.",
     "recognize": ["parentheses", "brackets", "matching", "nested",
                   "evaluate expression", "undo", "min stack"],
     "template": "pairs = {')': '(', ']': '[', '}': '{'}\nstack = []\n"
                 "for ch in s:\n    if ch in pairs:\n"
                 "        if not stack or stack.pop() != pairs[ch]: "
                 "return False\n    else: stack.append(ch)\n"
                 "return not stack",
     "mistakes": ["Popping an empty stack", "Skipping the final empty check"],
     "say": "The structure is nested, so the most recent unclosed item must "
            "resolve next: a stack. O(n) time and space.",
     "examples": ["Valid Parentheses", "Min Stack",
                  "Evaluate Reverse Polish Notation"]},
    {"id": "monostack", "name": "Monotonic Stack",
     "signal": "Next greater / next smaller element",
     "complexity": "O(n)", "ask": "Am I waiting for something bigger?",
     "model": "A stack kept sorted. A new element that breaks the order pops "
              "everything it outranks, and is their answer.",
     "recognize": ["next greater", "next smaller", "warmer", "histogram",
                   "span", "stock span"],
     "template": "res = [0] * n\nstack = []\nfor i, t in enumerate(a):\n"
                 "    while stack and a[stack[-1]] < t:\n"
                 "        j = stack.pop(); res[j] = i - j\n"
                 "    stack.append(i)",
     "mistakes": ["Storing values when you need indices",
                  "Wrong comparison direction for the variant"],
     "say": "Each element waits for the first larger one. A decreasing stack "
            "of indices resolves them; each index is pushed and popped once.",
     "examples": ["Daily Temperatures", "Largest Rectangle in Histogram",
                  "Car Fleet"]},
    {"id": "linked", "name": "Linked List Manipulation",
     "signal": "Rewire pointers in place with O(1) extra space",
     "complexity": "O(n)", "ask": "What must I hold before I overwrite?",
     "model": "Save next, rewire, advance. A dummy head removes the "
              "first-node special case.",
     "recognize": ["reverse", "merge two lists", "linked list",
                   "remove node", "reorder"],
     "template": "prev, cur = None, head\nwhile cur:\n"
                 "    nxt = cur.next\n    cur.next = prev\n"
                 "    prev, cur = cur, nxt\nreturn prev",
     "mistakes": ["Overwriting .next before saving it",
                  "Returning head instead of prev"],
     "say": "Reverse in place with three pointers, saving next before "
            "overwriting the link. O(n) time, O(1) space.",
     "examples": ["Reverse Linked List", "Merge Two Sorted Lists",
                  "Reorder List"]},
    {"id": "treedfs", "name": "Tree DFS",
     "signal": "Path, depth, subtree property, or ancestor",
     "complexity": "O(n)", "ask": "What does each child return?",
     "model": "Recursion is the traversal. Decide what a subtree returns to "
              "its parent and what gets passed down.",
     "recognize": ["depth", "height", "diameter", "path sum", "ancestor",
                   "validate bst", "subtree", "binary tree"],
     "template": "def dfs(node):\n    if not node: return 0\n"
                 "    l, r = dfs(node.left), dfs(node.right)\n"
                 "    return 1 + max(l, r)",
     "mistakes": ["Missing the None base case",
                  "Validating a BST against the parent only"],
     "say": "Post-order DFS: each call returns its subtree height and I "
            "update a running best on the way up. O(n), O(h) stack.",
     "examples": ["Maximum Depth of Binary Tree", "Diameter of Binary Tree",
                  "Validate Binary Search Tree"]},
    {"id": "treebfs", "name": "Tree BFS",
     "signal": "Level by level, or shortest depth",
     "complexity": "O(n)", "ask": "Does the level matter?",
     "model": "A queue processed one full level at a time: snapshot len(q).",
     "recognize": ["level order", "right side view", "minimum depth",
                   "per level", "zigzag"],
     "template": "q = deque([root])\nwhile q:\n"
                 "    for _ in range(len(q)):\n        node = q.popleft()\n"
                 "        # visit, enqueue children",
     "mistakes": ["Not snapshotting len(q)", "list.pop(0) instead of deque"],
     "say": "Levels matter, so BFS with a queue, one level per iteration. "
            "O(n) time, O(width) space.",
     "examples": ["Binary Tree Level Order Traversal",
                  "Binary Tree Right Side View"]},
    {"id": "graph", "name": "Graph Traversal",
     "signal": "Connectivity, islands, or shortest unweighted path",
     "complexity": "O(V+E)", "ask": "BFS for shortest, DFS for reachability?",
     "model": "A grid is a graph of 4-neighbours. BFS gives shortest path "
              "when edges weigh 1; DFS tells you what's reachable.",
     "recognize": ["island", "grid", "flood fill", "connected components",
                   "shortest path", "reach", "rotting", "graph"],
     "template": "q = deque(starts); seen = set(starts)\nwhile q:\n"
                 "    r, c = q.popleft()\n"
                 "    for nr, nc in neighbours(r, c):\n"
                 "        if ok(nr, nc) and (nr, nc) not in seen:\n"
                 "            seen.add((nr, nc)); q.append((nr, nc))",
     "mistakes": ["Marking visited on pop instead of push",
                  "Recursion depth on large grids"],
     "say": "Model the grid as a graph; edges weigh one, so BFS gives the "
            "shortest path. Mark visited on enqueue. O(rows x cols).",
     "examples": ["Number of Islands", "Rotting Oranges", "Clone Graph"]},
    {"id": "toposort", "name": "Topological Sort",
     "signal": "Dependencies, ordering, prerequisites",
     "complexity": "O(V+E)", "ask": "Is there a cycle?",
     "model": "Repeatedly take a node with no remaining dependencies. If the "
              "graph won't empty, there's a cycle.",
     "recognize": ["prerequisite", "course schedule", "build order",
                   "dependency", "ordering possible", "alien dictionary"],
     "template": "q = deque(u for u in g if indeg[u] == 0)\norder = []\n"
                 "while q:\n    u = q.popleft(); order.append(u)\n"
                 "    for v in g[u]:\n        indeg[v] -= 1\n"
                 "        if indeg[v] == 0: q.append(v)",
     "mistakes": ["Not checking len(order) == nodes",
                  "Edges built in the wrong direction"],
     "say": "It's a dependency graph, so Kahn's algorithm; a short output "
            "means a cycle. O(V + E).",
     "examples": ["Course Schedule", "Course Schedule II",
                  "Alien Dictionary"]},
    {"id": "unionfind", "name": "Union Find",
     "signal": "Dynamic connectivity, merging groups",
     "complexity": "~O(1) amortized", "ask": "Already connected?",
     "model": "Each set has a representative; path compression makes find "
              "nearly constant.",
     "recognize": ["same group", "connected components", "redundant",
                   "merge accounts", "provinces", "cycle undirected"],
     "template": "def find(x):\n    while parent[x] != x:\n"
                 "        parent[x] = parent[parent[x]]; x = parent[x]\n"
                 "    return x",
     "mistakes": ["Comparing elements instead of roots",
                  "Skipping path compression"],
     "say": "Union returns false when two nodes already share a root, which "
            "is exactly the cycle condition.",
     "examples": ["Number of Provinces", "Redundant Connection",
                  "Accounts Merge"]},
    {"id": "heap", "name": "Heap / Top-K",
     "signal": "K largest/smallest, or a streaming median",
     "complexity": "O(n log k)", "ask": "Do I need the whole sort, or just K?",
     "model": "Keep a heap of size K and evict the worst; never sort it all.",
     "recognize": ["top k", "kth largest", "k closest", "most frequent",
                   "median", "merge k", "priority"],
     "template": "heap = []\nfor x in nums:\n    heapq.heappush(heap, x)\n"
                 "    if len(heap) > k: heapq.heappop(heap)\nreturn heap[0]",
     "mistakes": ["heapq is a MIN heap: negate for max",
                  "Full sort when k is small"],
     "say": "Only the top K matter, so a size-K min-heap: O(n log k).",
     "examples": ["Kth Largest Element", "Top K Frequent Elements",
                  "Find Median from Data Stream"]},
    {"id": "intervals", "name": "Intervals",
     "signal": "Overlapping ranges, meetings, merging",
     "complexity": "O(n log n)", "ask": "Sort by start or by end?",
     "model": "Sort, then one sweep decides extend vs start new.",
     "recognize": ["interval", "overlap", "meeting", "rooms", "merge ranges",
                   "schedule"],
     "template": "intervals.sort()\nout = []\nfor s, e in intervals:\n"
                 "    if out and s <= out[-1][1]: "
                 "out[-1][1] = max(out[-1][1], e)\n"
                 "    else: out.append([s, e])",
     "mistakes": ["Sorting by the wrong field", "Forgetting max() on merge"],
     "say": "Sort by start and sweep once, extending the current interval "
            "on overlap. O(n log n).",
     "examples": ["Merge Intervals", "Insert Interval", "Meeting Rooms II"]},
    {"id": "backtrack", "name": "Backtracking",
     "signal": "Enumerate all combinations / permutations / paths",
     "complexity": "Exponential", "ask": "What is one choice, and its undo?",
     "model": "Choose, explore, un-choose while walking a decision tree.",
     "recognize": ["all subsets", "permutations", "combinations",
                   "every valid", "n queens", "word search", "sudoku"],
     "template": "def bt(start, path):\n    res.append(path[:])\n"
                 "    for i in range(start, len(nums)):\n"
                 "        path.append(nums[i]); bt(i + 1, path); path.pop()",
     "mistakes": ["Appending path instead of path[:]", "Forgetting to undo"],
     "say": "Small n means exponential is fine: choose, recurse, undo, and "
            "prune as soon as a branch can't win.",
     "examples": ["Subsets", "Combination Sum", "Permutations",
                  "Word Search"]},
    {"id": "dp", "name": "Dynamic Programming",
     "signal": "Overlapping subproblems and optimal substructure",
     "complexity": "O(states x transition)",
     "ask": "What does dp[i] mean, in one sentence?",
     "model": "Name the state, write the transition, fix the base case, "
              "pick the order. Never memorise solutions.",
     "recognize": ["number of ways", "minimum cost", "maximum", "can i make",
                   "longest increasing", "edit distance", "knapsack",
                   "climbing stairs", "house robber"],
     "template": "# STATE dp[i] = best using first i items\n"
                 "# TRANSITION dp[i] = max(dp[i-1], dp[i-2] + nums[i-1])\n"
                 "# BASE dp[0] = 0\n# ORDER increasing i",
     "mistakes": ["Coding before naming the state",
                  "Iterating before dependencies are ready"],
     "say": "Recursion repeats subproblems, so dp[i] is the best for the "
            "first i items; take or skip each one. O(n), O(1) with rolling "
            "variables.",
     "examples": ["House Robber", "Coin Change",
                  "Longest Increasing Subsequence", "Unique Paths"]},
    {"id": "greedy", "name": "Greedy",
     "signal": "A locally optimal choice is provably globally optimal",
     "complexity": "O(n log n)", "ask": "Can I prove the local choice is safe?",
     "model": "Take the best option now and never reconsider, only when an "
              "exchange argument proves it safe.",
     "recognize": ["jump game", "gas station", "fewest", "maximum number of",
                   "task scheduler", "reach the end"],
     "template": "reach = 0\nfor i, j in enumerate(nums):\n"
                 "    if i > reach: return False\n"
                 "    reach = max(reach, i + j)\nreturn True",
     "mistakes": ["Greedy where DP is needed (arbitrary coin change)",
                  "Not stating why the choice is safe"],
     "say": "An exchange argument shows the greedy choice is never worse, so "
            "sort and take the best each step.",
     "examples": ["Jump Game", "Gas Station", "Task Scheduler"]},
    {"id": "trie", "name": "Trie",
     "signal": "Prefix queries over a set of words",
     "complexity": "O(word length)", "ask": "Do many strings share prefixes?",
     "model": "A tree of characters: lookup costs the word length, not the "
              "dictionary size.",
     "recognize": ["prefix", "autocomplete", "starts with", "dictionary",
                   "word search ii", "wildcard"],
     "template": "node = root\nfor ch in word:\n"
                 "    node = node.kids.setdefault(ch, Trie())\n"
                 "node.end = True",
     "mistakes": ["No end-of-word flag", "Not pruning in Word Search II"],
     "say": "Shared prefixes make a trie the right index: membership in "
            "O(word length).",
     "examples": ["Implement Trie", "Design Add and Search Words",
                  "Word Search II"]},
    {"id": "matrix", "name": "Matrix Traversal",
     "signal": "2D grid walked in a specific geometry",
     "complexity": "O(m x n)", "ask": "What are the boundaries?",
     "model": "Mostly index bookkeeping: write the boundaries before coding.",
     "recognize": ["spiral", "rotate image", "matrix", "set zeroes",
                   "diagonal", "transpose"],
     "template": "top, bot, left, right = 0, m-1, 0, n-1\n"
                 "while top <= bot and left <= right:\n"
                 "    # four passes, re-check bounds before passes 3 and 4",
     "mistakes": ["Not re-checking bounds mid-spiral",
                  "Copying when it says in place"],
     "say": "Track four shrinking boundaries and re-check them before the "
            "reverse passes.",
     "examples": ["Spiral Matrix", "Rotate Image", "Set Matrix Zeroes"]},
    {"id": "bits", "name": "Bit Manipulation",
     "signal": "XOR tricks, counting bits, subsets as masks",
     "complexity": "O(1) or O(n)", "ask": "Can XOR cancel the pairs?",
     "model": "XOR cancels pairs, AND masks, bits encode subsets.",
     "recognize": ["single number", "appears twice", "bits", "xor",
                   "missing number", "power of two"],
     "template": "res = 0\nfor x in nums: res ^= x   # pairs cancel",
     "mistakes": ["Python ints are unbounded: mask for 32-bit",
                  "& binds looser than =="],
     "say": "XOR is self-cancelling, so XOR-ing everything leaves the "
            "unpaired value. O(n), O(1) space.",
     "examples": ["Single Number", "Counting Bits", "Missing Number"]},
    {"id": "design", "name": "Design / Simulation",
     "signal": "Build a data structure to a spec",
     "complexity": "Usually O(1) per op", "ask": "Which ops must be O(1)?",
     "model": "Combine structures so every required op is cheap: usually a "
              "hash map plus one structure for order.",
     "recognize": ["design", "lru", "lfu", "implement class", "o(1)",
                   "cache", "iterator"],
     "template": "# LRU = dict(key -> node) + doubly linked list by recency",
     "mistakes": ["Not asking which ops must be O(1)",
                  "Forgetting to update the map on eviction"],
     "say": "get and put must both be O(1), so a hash map for lookup plus a "
            "doubly linked list for recency.",
     "examples": ["LRU Cache", "Min Stack", "Implement Queue using Stacks"]},
]

BY_ID = {p["id"]: p for p in PATTERNS}
