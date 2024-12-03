package com.example.mentos.Login;

import android.util.Log;

import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;

import org.json.JSONException;
import org.json.JSONObject;

public class LoginRequest extends JsonObjectRequest {

    private static final String LOGIN_REQUEST_URL = "http://52.79.234.36:5001/login";

    public LoginRequest(String email, String password, Response.Listener<JSONObject> listener) throws JSONException {
        super(Method.POST, LOGIN_REQUEST_URL, createRequestBody(email, password), listener, new Response.ErrorListener() {
            @Override
            public void onErrorResponse(VolleyError error) {
                // 네트워크 오류 로그
                Log.e("LoginRequest", "Error: " + error.toString());
                error.printStackTrace();
            }
        });

        // 파라미터 로그
        Log.d("LoginRequest", "Params: " + createRequestBody(email, password).toString());
    }

    private static JSONObject createRequestBody(String email, String password) throws JSONException {
        JSONObject requestBody = new JSONObject();
        requestBody.put("email", email);
        requestBody.put("password", password);
        return requestBody;
    }
}