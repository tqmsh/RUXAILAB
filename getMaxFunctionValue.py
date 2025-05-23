from collections import defaultdict

class Tarjan:
    """A modular implementation of Tarjan's algorithm for graph analysis."""
    
    def __init__(self, n, edges=None):
        """
        Initialize Tarjan algorithm for a graph with n nodes.
        
        Args:
            n: Number of nodes (0-indexed)
            edges: Optional list of edges as (u, v) pairs
        """
        self.n = n
        self.graph = defaultdict(list)
        self.time = 0
        
        # Add edges if provided
        if edges:
            for u, v in edges:
                self.add_edge(u, v)
    
    def add_edge(self, u, v):
        """Add an undirected edge between u and v."""
        self.graph[u].append(v)
        self.graph[v].append(u)
    
    def add_directed_edge(self, u, v):
        """Add a directed edge from u to v."""
        self.graph[u].append(v)
    
    def find_articulation_points(self):
        """
        Find all articulation points (cut vertices) in the graph.
        
        Returns:
            List of articulation points
        """
        visited = [False] * self.n
        disc = [-1] * self.n  # Discovery time
        low = [-1] * self.n   # Earliest visited vertex
        parent = [-1] * self.n
        ap = [False] * self.n  # To store articulation points
        
        def dfs(u):
            children = 0
            visited[u] = True
            self.time += 1
            disc[u] = low[u] = self.time
            
            for v in self.graph[u]:
                if not visited[v]:
                    children += 1
                    parent[v] = u
                    dfs(v)
                    
                    # Check if subtree rooted at v has a connection to ancestor of u
                    low[u] = min(low[u], low[v])
                    
                    # Case 1: u is root and has multiple children
                    if parent[u] == -1 and children > 1:
                        ap[u] = True
                    
                    # Case 2: u is not root and low value of one of its children is >= disc value of u
                    if parent[u] != -1 and low[v] >= disc[u]:
                        ap[u] = True
                
                # Update low value of u for parent function calls
                elif v != parent[u]:
                    low[u] = min(low[u], disc[v])
        
        # Call DFS for each unvisited vertex
        for i in range(self.n):
            if not visited[i]:
                dfs(i)
        
        return [i for i in range(self.n) if ap[i]]
    
    def find_bridges(self):
        """
        Find all bridges in the graph.
        
        Returns:
            List of bridges as (u, v) pairs
        """
        visited = [False] * self.n
        disc = [-1] * self.n
        low = [-1] * self.n
        parent = [-1] * self.n
        bridges = []
        
        def dfs(u):
            visited[u] = True
            self.time += 1
            disc[u] = low[u] = self.time
            
            for v in self.graph[u]:
                if not visited[v]:
                    parent[v] = u
                    dfs(v)
                    
                    # Check if the edge u-v is a bridge
                    low[u] = min(low[u], low[v])
                    if low[v] > disc[u]:
                        bridges.append((u, v))
                
                elif v != parent[u]:
                    low[u] = min(low[u], disc[v])
        
        for i in range(self.n):
            if not visited[i]:
                dfs(i)
                
        return bridges
    
    def find_scc(self):
        """
        Find all strongly connected components (SCCs) in the graph.
        Note: The graph should have directed edges for this function.
        
        Returns:
            List of SCCs, where each SCC is a list of nodes
        """
        stack = []
        visited = [False] * self.n
        sccs = []
        
        # First DFS to fill the stack
        def fill_order(u):
            visited[u] = True
            for v in self.graph[u]:
                if not visited[v]:
                    fill_order(v)
            stack.append(u)
        
        # Create the reversed graph
        def transpose():
            t = Tarjan(self.n)
            for u in range(self.n):
                for v in self.graph[u]:
                    t.add_directed_edge(v, u)
            return t
        
        # Second DFS to find SCCs
        def collect_scc(graph, u, visited, component):
            visited[u] = True
            component.append(u)
            for v in graph.graph[u]:
                if not visited[v]:
                    collect_scc(graph, v, visited, component)
        
        # Fill the stack with vertices based on finish times
        for i in range(self.n):
            if not visited[i]:
                fill_order(i)
        
        # Create the transposed graph
        transposed = transpose()
        
        # Reset visited array for the second DFS
        visited = [False] * self.n
        
        # Process vertices in order defined by the stack
        while stack:
            u = stack.pop()
            if not visited[u]:
                component = []
                collect_scc(transposed, u, visited, component)
                sccs.append(component)
        
        return sccs
    
    def find_biconnected_components(self):
        """
        Find all biconnected components in the graph.
        
        Returns:
            List of biconnected components, where each component is a list of edges
        """
        visited = [False] * self.n
        disc = [-1] * self.n
        low = [-1] * self.n
        parent = [-1] * self.n
        stack = []
        components = []
        
        def dfs(u):
            visited[u] = True
            self.time += 1
            disc[u] = low[u] = self.time
            children = 0
            
            for v in self.graph[u]:
                # If v is not visited, make it a child of u in DFS tree
                if not visited[v]:
                    children += 1
                    parent[v] = u
                    stack.append((u, v))
                    dfs(v)
                    
                    # Check if subtree rooted at v has a connection to ancestor of u
                    low[u] = min(low[u], low[v])
                    
                    # If u is an articulation point or root, pop all edges from stack till (u, v)
                    if (parent[u] == -1 and children > 1) or (parent[u] != -1 and low[v] >= disc[u]):
                        component = []
                        while True:
                            edge = stack.pop()
                            component.append(edge)
                            if edge == (u, v):
                                break
                        components.append(component)
                
                # Update low value of u for parent function calls
                elif v != parent[u] and disc[v] < disc[u]:
                    low[u] = min(low[u], disc[v])
                    stack.append((u, v))
        
        for i in range(self.n):
            if not visited[i]:
                dfs(i)
                # If stack is not empty, it contains one biconnected component
                if stack:
                    components.append(stack[:])
                    stack.clear()
        
        return components


class Solution:
    def minDays(self, grid):
        """
        Determine the minimum number of days to disconnect an island.
        
        Returns:
            0 if already disconnected or no island
            1 if removing one cell can disconnect the island
            2 otherwise
        """
        n, m = len(grid), len(grid[0])
        
        # Check if grid is empty or already disconnected
        def count_islands():
            visited = [[False] * m for _ in range(n)]
            count = 0
            
            def dfs(i, j):
                if (i < 0 or i >= n or j < 0 or j >= m or 
                    grid[i][j] == 0 or visited[i][j]):
                    return
                
                visited[i][j] = True
                
                # Check all 4 directions
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    dfs(i + di, j + dj)
            
            for i in range(n):
                for j in range(m):
                    if grid[i][j] == 1 and not visited[i][j]:
                        count += 1
                        dfs(i, j)
            
            return count
        
        # First check if island is already disconnected (0 or >1 islands)
        island_count = count_islands()
        if island_count != 1:
            return 0
        
        # Build graph for Tarjan's algorithm
        land_cells = []
        for i in range(n):
            for j in range(m):
                if grid[i][j] == 1:
                    land_cells.append((i, j))
        
        # Special case: if there's only one land cell
        if len(land_cells) == 1:
            return 1
        
        # Create node index mapping
        node_map = {}
        for idx, (i, j) in enumerate(land_cells):
            node_map[(i, j)] = idx
        
        # Create Tarjan instance
        tarjan = Tarjan(len(land_cells))
        
        # Add edges
        for i, j in land_cells:
            u = node_map[(i, j)]
            
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + di, j + dj
                if (0 <= ni < n and 0 <= nj < m and 
                    grid[ni][nj] == 1):
                    v = node_map[(ni, nj)]
                    tarjan.add_edge(u, v)
        
        # Check if there's an articulation point
        articulation_points = tarjan.find_articulation_points()
        
        if articulation_points:
            return 1  # Removing any articulation point will disconnect the island
        
        return 2  # Need to remove at least 2 cells