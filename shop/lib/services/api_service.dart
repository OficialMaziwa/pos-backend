import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'https://pos-backend2.onrender.com/api';
  
  static Future<Map<String, dynamic>> login(String email, String password) async {
    print('=== LOGIN ===');
    print('URL: $baseUrl/auth/login');
    
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'email': email, 'password': password}),
    );
    
    print('Login status: ${response.statusCode}');
    print('Login body: ${response.body}');
    
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Login failed: ${response.statusCode}');
    }
  }

  static Future<Map<String, dynamic>> getDashboard(String token) async {
    print('=== DASHBOARD API ===');
    print('Token: $token');
    print('URL: $baseUrl/reports/dashboard');
    
    final response = await http.get(
      Uri.parse('$baseUrl/reports/dashboard'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );
    
    print('Dashboard status: ${response.statusCode}');
    print('Dashboard response: ${response.body}');
    
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else if (response.statusCode == 401) {
      throw Exception('Unauthorized: Invalid or expired token');
    } else {
      throw Exception('Failed to load dashboard: ${response.statusCode}');
    }
  }
}