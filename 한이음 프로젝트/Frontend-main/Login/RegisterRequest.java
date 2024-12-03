package com.example.mentos.Login;

import android.util.Log;

import com.android.volley.DefaultRetryPolicy;
import com.android.volley.Response;
import com.android.volley.RetryPolicy;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.HashMap;
import java.util.Map;

public class RegisterRequest extends JsonObjectRequest {

    private static final String REGISTER_REQUEST_URL = "http://52.79.234.36:5001/signup";

    public RegisterRequest(String email, String password, String gender, String birthdate, Response.Listener<JSONObject> listener) throws JSONException {
        super(Method.POST, REGISTER_REQUEST_URL, createRequestBody(email, password, gender, birthdate), listener, new Response.ErrorListener() {
            @Override
            public void onErrorResponse(VolleyError error) {
                // 네트워크 오류 로그
                Log.e("RegisterRequest", "Error: " + error.toString());
                error.printStackTrace();
            }
        });

        // 파라미터 로그
        Log.d("RegisterRequest", "Params: " + createRequestBody(email, password, gender, birthdate).toString());
    }

    private static JSONObject createRequestBody(String email, String password, String gender, String birthdate) throws JSONException {
        JSONObject requestBody = new JSONObject();
        requestBody.put("email", email);
        requestBody.put("password", password);
        requestBody.put("gender", gender);
        requestBody.put("birthdate", birthdate);
        return requestBody;
    }

//    @Override
//    public RetryPolicy getRetryPolicy() {
//        return new DefaultRetryPolicy(
//                5000,
//                DefaultRetryPolicy.DEFAULT_MAX_RETRIES,
//                DefaultRetryPolicy.DEFAULT_BACKOFF_MULT);
//    }
}
